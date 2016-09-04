# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import datetime, decimal
import logging

from django.contrib.sites.models import Site
from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone as djtimezone
from django.core.urlresolvers import reverse
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


from dashboard.profile.localflavor_cn.provinces import CN_PROVINCE_CHOICES
from dashboard.profile.models import Membership
from dashboard.listing.models import Item, Fund
from accounts.signals import user_activated as user_activated_signal
from accounts.backends.default.views import ActivationView
from payment.alipay.models import AlipayPartnerTrade, AlipayDirectPay
from payment.alipay.modelfields import AlipayPriceField, AlipayTotalFeeField, AlipayLogisticsFeeField
from exceptions import CreateOrderException
from signals import *
from signal_handlers import *
from modelfields import OrderStatusField, OrderStatus


logger = logging.getLogger('site.models.orders')


class OrderManager(models.Manager):
	"""
	"""

	def create_order(self, buyer, seller, comment, social_platform, body, merchandise, quantity):

		_CREATE_ORDER_SUCCESS = False
		_CREATE_ORDER_NORMAL_FAIL = False
		_FAIL_REASON = None
		
		with transaction.commit_manually():
			try:
				sid = transaction.savepoint() # item reserve transaction savepoint

				logger.info('preparing user info...')

				title = merchandise.name # title should be a combination of item and it's owner
				price = merchandise.price
				# order location
				location = buyer.userprofile.province

				if not seller.is_active:
					raise CreateOrderException('卖家已经注销帐户')
				if not buyer.is_active:
					raise Exception('买家删除帐户，不建立交易')

				logger.info('preparing merchandise info...')
				
				if isinstance(merchandise, Item):
					# 确定买家没有超过用户购买限制
					number_purchased = Order.objects.number_merchandise_purchased_by_buyer(buyer, merchandise)
					if number_purchased + quantity > merchandise.purchase_limit:
						raise CreateOrderException("买家购买总数: %s 超过了物品购买限制: %s" % (number_purchased+quantity, merchandise.purchase_limit))
					# 确定物品购买数量
					retrived_quantity, merchandise, msg = merchandise.__class__.objects.retrive_item(merchandise, quantity) # 确保购买数量小于用户购买限制
					if retrived_quantity <= 0:
						raise CreateOrderException(msg)
					else:
						quantity = retrived_quantity
				
				# 物流价格
				if hasattr(merchandise, 'logistics_fee'):
					logistics_fee = merchandise.logistics_fee
				else:
					# 其他商品的物流价格
					logistics_fee = 0
				
				total_fee = quantity * price + logistics_fee
				# service charge
				service_charge = self.determine_service_charge(buyer, total_fee)

				logger.warning('Order data prepare success, starting to create order...')

				order = self.create(buyer=buyer, 
									seller=seller,
									merchandise_object=merchandise, 
									social_platform=social_platform,
									title=title,
									comment=comment,
									location=location,
									price=price,
									logistics_fee=logistics_fee,
									quantity=quantity,
									service_charge=service_charge,
									total_fee=total_fee,
									status=OrderStatus.CREATED)

				print 'order create success... start initiating payment...'

				payment, msg = order.initiate_payment()
				if payment:
					transaction.savepoint_commit(sid)
					order.send_verification()
					
				else:
					raise CreateOrderException(msg)

			except CreateOrderException, err:
				# 创建支付宝担保交易失败
				logger.warning("%r fail:%s" % (self, err))
				# 发送创建失败信息
				_FAIL_REASON = err.reason
				_CREATE_ORDER_NORMAL_FAIL = True
				transaction.savepoint_rollback(sid)

			except Exception, err:
				# 非正常原因失败
				logger.critical("%r hard fail:%s" % (self, err))
				transaction.savepoint_rollback(sid)

			finally:
				transaction.commit()

		if _CREATE_ORDER_NORMAL_FAIL:
			create_order_fail_signal.send(sender=self.__class__, 
													buyer=buyer,
													title=title or None,
													comment=comment,
													social_platform=social_platform,
													quantity=quantity,
													reason=_FAIL_REASON)	



	def determine_service_charge(self, buyer, total_fee):
		"""
		返回收取用户的提成
		"""
		if Membership.objects.is_premium(buyer):
			# 高级用户
			service_charge = total_fee * decimal.Decimal(0.03)
		elif Membership.objects.is_enterprise(buyer):
			# 企业用户
			service_charge = total_fee * decimal.Decimal(0.03)
		else:
			# 普通用户
			service_charge = total_fee * decimal.Decimal(0.05)
		return service_charge


	def number_merchandise_purchased_by_buyer(self, buyer, merchandise, **kwargs):
		try:
			merchandise_type = ContentType.objects.get_for_model(merchandise)
			orders = Order.objects.filter(buyer=buyer, merchandise_type__pk=merchandise_type.pk,
                           merchandise_id=merchandise.pk, **kwargs)
			total_number = 0
			for order in orders:
				total_number += order.quantity
			return total_number

		except Exception, err:
			logger.critical(u"%r: number of %r purchased by %r err: %s" % (self, merchandise, buyer, err))
			return 0

	def get_sell_orders(self, user, **kwargs):
		"""
		找出所有用户的sell orders, 并且默认verified orders
		如果没有则返回空 queryset
		"""
		#TODO: filter out payment unverified orders
		return self.filter(seller=user, **kwargs).order_by('start_time')

	def get_buy_orders(self, user, **kwargs):
		"""
		找出所有用户的buy orders, 默认verified无关,并且order没有过期
		TODO: order 过期设置
		"""
		return self.filter(buyer=user, **kwargs).order_by('start_time')


	def delete_expired_orders(self):
		"""
		删除过期的order, 在order没有被认证的情况下
		"""
		for orders in self.all():
			try:
				if not order.payment_verified and order.is_expired:
					order.delete()
			except Exception, err:
				logger.critical(u" delete %r fail, reason:%s" % (order, err))




class Order(models.Model):
	"""
	"""

	# Order users
	seller = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="%(class)s_seller", null=True, on_delete=models.SET_NULL, editable=False)
	buyer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="%(class)s_buyer", null=True, on_delete=models.SET_NULL, editable=False)
	# order merchandise
	merchandise_limit = models.Q(app_label = 'listing', model = 'PhysicalItem') | \
			models.Q(app_label = 'listing', model = 'DigitalItem') | \
			models.Q(app_label = 'listing', model = 'EventItem') | \
			models.Q(app_label = 'listing', model = 'DonationFund') | \
			models.Q(app_label = 'listing', model = 'PaybackFund')

	merchandise_type = models.ForeignKey(ContentType, limit_choices_to=merchandise_limit, related_name='merchandise_type', null=False)
	merchandise_id = models.PositiveIntegerField()
	merchandise_object = generic.GenericForeignKey('merchandise_type', 'merchandise_id')
	# order payment
	payment_limit = models.Q(app_label = 'alipay', model = 'AlipayPartnerTrade') | \
			models.Q(app_label = 'listing', model = 'AlipayDirectPay')


	payment_type = models.ForeignKey(ContentType, limit_choices_to = payment_limit, related_name='payment_type', null=True)
	payment_id = models.PositiveIntegerField(null=True)
	payment_object = generic.GenericForeignKey('payment_type', 'payment_id')


	# order details
	status = OrderStatusField(null=False, blank=False, editable=True)
	price = AlipayPriceField(null=False, editable=False)
	quantity = models.PositiveIntegerField(null=False, editable=False)
	service_charge = AlipayPriceField(null=False, editable=False)
	logistics_fee = AlipayLogisticsFeeField(null=False, editable=False)
	total_fee = AlipayTotalFeeField(null=False, editable=False)

	# Order Info
	social_platform = models.ForeignKey('platforms.SocialPlatform', null=True, on_delete=models.SET_NULL, editable=True)
	title = models.CharField(max_length=50, null=False, blank=False, editable=True) # Title from the post
	comment = models.CharField(max_length=100, null=False, editable=False) # Comment from the post comment
	comment_time = models.DateTimeField(null=True, editable=False)
	location = models.CharField(max_length=100, choices=CN_PROVINCE_CHOICES, null=True, blank=False, editable=True)
	# Order times, 网站时间
	start_time = models.DateTimeField(null=False, editable=True) # 网站时间
	expire_time = models.DateTimeField(null=False, editable=True) # 网站时间
	finish_time = models.DateTimeField(null=True, editable=True) # 网站时间
	
	# Order manager
	objects = OrderManager() # to be inherited



	def __unicode__(self):
		return u"%s(%s)" % (self.title, self.id)

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)


	def get_absolute_url(self):
		return reverse('dashboard:orders:order-detail', args=[str(self.pk)])


	def save(self, *args, **kwargs):
		if not self.id:
			# always store UTC time in database
			expires_in = kwargs.pop('expires_in', 2) # 过期时间，默认为2小时
			self.start_time = djtimezone.now()
			self.expire_time = self.start_time + datetime.timedelta(hours=expires_in) # 默认2天expire时间
		super(Order, self).save(*args, **kwargs)


	@property
	def payment_verified(self):
		if self.status == OrderStatus.PAYMENT_VERIFIED or \
			self.status == OrderStatus.SUCCEED or \
			self.status == OrderStatus.SHIPPMENT_CONFIRMMED or \
			self.status == OrderStatus.SHIPPMENT_RECEIVED:

			return True
		else:
			return False

	@property
	def shippment_confirmmed(self):
		#STUB
		if 	self.status == OrderStatus.SUCCEED or \
			self.status == OrderStatus.SHIPPMENT_CONFIRMMED or \
			self.status == OrderStatus.SHIPPMENT_RECEIVED:

			return True
		else:
			return False


	@property
	def is_expired(self):
		"""
		检查这个Order是否expire, override base class method
		"""
		return not self.payment_verified and djtimezone.now() >= self.expire_time


	@property
	def is_succeed(self):
		"""
		"""
		if self.status == OrderStatus.SUCCEED:
			return True
		else:
			return False

	@property
	def is_failed(self):
		"""
		"""
		if self.status == OrderStatus.FAILED:
			return True
		else:
			return False


	@property
	def is_finished(self):
		"""
		通过查看finish_time是否设置来返回order是否结束
		"""
		#print self.finish_time
		if self.finish_time or self.is_succeed or self.is_failed:
			return True
		else:
			return False


	def send_verification(self, created=True):
		"""
		"""
		if not self.payment_verified and not self.is_finished:
			create_order_success_signal.send_robust(sender=self.__class__, 
													order=self,
													payment=self.payment_object)


	def get_buyer_cancel_url(self):
		"""
		取消交易url,只有在买家未认证的情况下才可以取消交易
		"""
		return reverse('dashboard:orders:cancel-buyer', args=[str(self.pk)])


	def get_absolute_buyer_cancel_url(self):
		"""
		用来给外围用户进入网站的absolute url
		"""

		absolute_url = u"http://%s%s" % (Site.objects.get_current(), self.get_buyer_cancel_url())

		return absolute_url


	def get_seller_cancel_url(self):
		"""
		卖家取消交易url,只有在买家已经认证的情况下并且在有效期内才可以取消交易
		"""
		return reverse('dashboard:orders:cancel-seller', args=[str(self.pk)])


	def get_verify_url(self):
		"""
		买家认证交易url
		"""
		return reverse('dashboard:orders:verify', args=[str(self.pk)])


	def get_absolute_verify_url(self):
		"""
		用来给外围用户进入网站的absolute url
		"""
		absolute_url = u"http://%s%s" % (Site.objects.get_current(), self.get_verify_url())

		return absolute_url



	def get_payment_verify_url(self):
		"""
		买家认证交易支付url
		"""
		if self.payment_object.verify_url:
			return self.payment_object.verify_url
		else:
			return self.payment_object.build_verify_url(write_to_db=True)


	def get_shippment_confirm_url(self):
		"""
		卖家认证寄货url
		"""
		# STUB
		return None

	def is_buyer(self, user):
		"""
		检查用户是买家还是卖家
		"""
		if user.id == self.buyer_id:
			return True
		else:
			return False


	def is_seller(self, user):
		"""
		检查用户是买家还是卖家
		"""
		if user.id == self.seller_id:
			return True
		else:
			return False

	def initiate_payment(self):
		"""
		"""
		if isinstance(self.merchandise_object, Item):
			# create partner trade payment
			payment, msg = AlipayPartnerTrade.objects.create_payment(
					xmf_order=self,
					buyer=self.buyer, 
					seller=self.seller,
					item=self.merchandise_object, 
					body=self.title,
					price=self.price,
					logistics_fee=self.logistics_fee,
					quantity=self.quantity,
					total_fee=self.total_fee)

		elif isinstance(self.merchandise_object, Fund):
			payment, msg = AlipayDirectPay.objects.create_payment(
					xmf_order=self,
					buyer=self.buyer, 
					seller=self.seller, 
					body=self.title,
					fund=self.merchandise_object,
					total_fee=self.total_fee)
		else:
			payment = None
			msg = u"交易物品不符合规范"

		if payment:
			self.payment_object = payment
			self.save(force_update=True)

		return payment, msg


	def cancel_by_buyer(self, user):
		if self.is_buyer(user):
			if self.payment_verified:
				return u"买家支付已经认证，无法取消交易"
			else:
				# 交易没有被认证并且交易没有结束
				self.delete()
				return u"买家取消交易成功"
		else:
			return u"用户不是买家，无权通过买家取消交易"


	def cancel_by_seller(self, user):
		if self.is_seller(user):
			return 'lalala'
		else:
			return u"用户不是卖家，无权通过卖家取消交易"

	def set_succeed(self):
		"""
		"""
		if not self.is_finished and self.payment_verified:
			self.status = OrderStatus.SUCCEED
			self.finish_time = djtimezone.now()
			self.save(force_update=True)
			return True
		else:
			return False

	def set_fail(self, reason):
		"""
		"""
		if not self.is_finished:
			self.status = OrderStatus.FAILED
			self.finish_time = djtimezone.now()
			self.save(force_update=True)
			return True
		else:
			return False




"""
交易创建信号连接
"""
# 连接支付宝担保交易创建成功信号
create_order_success_signal.connect(create_order_success_handler,
					sender=OrderManager,
					weak=False, 
					dispatch_uid='order.signals.create_order_success')

# 连接支付宝担保交易创建失败信号
create_order_fail_signal.connect(create_order_fail_handler,
					sender=OrderManager,
					weak=False, 
					dispatch_uid="order.signals.create_order_fail")




class UserOrderStat(models.Model):

	user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, null=False, blank=False, editable=False)
	successful_sell = models.PositiveIntegerField(null=False, default=0, editable=True)
	successful_buy = models.PositiveIntegerField(null=False, default=0, editable=True)
	fail_sell = models.PositiveIntegerField(null=False, default=0, editable=True)



@receiver(user_activated_signal, sender=ActivationView, weak=False, dispatch_uid="signals.user_activated.create_user_order_stat")
def create_user_order_stat(sender, user, request, *args, **kwargs):
	try:
		UserOrderStat.objects.create(user=user)
	except Exception, err:
		logger.critical(u"create %r's user order stat fail... reason:%s", (user, err))










