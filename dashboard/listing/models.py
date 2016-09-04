# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import os.path, uuid, logging, datetime, pytz

from django.conf import settings
from django.utils import timezone as djtimezone
from django.db import models
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.contrib.contenttypes import generic
from django.core.validators import MinValueValidator, MaxValueValidator, MaxLengthValidator


from siteutils.modelfields import TimeZoneField
from metadata.models import MetaData
from payment.alipay.modelfields import *
from signals import *
from modelfields import *
from dashboard.passbook.models import TicketPass, DigitalFilePass


logger = logging.getLogger('xiaomaifeng.listing')


if hasattr(settings, "AWS_SECRET_ACCESS_KEY"):
	try:
		from backends.S3Storage import S3Storage
		storage = S3Storage()
	except ImportError:
		raise S3BackendNotFound
else:
	storage = default_storage

"""
物品和筹资在设计中故意被分开成连个独立的数据模型，
而虚拟物品和实体物品则被归为物品，成为物品的subclass
设计中：添加捐款筹资和募集筹资两个筹资的subclass
"""


class ValidateOnSaveMixin:

	def save(self, force_insert=False, force_update=False, **kwargs):
		if not (force_insert or force_update):
			self.full_clean()
		super(ValidateOnSaveMixin, self).save(force_insert, force_update,
											  **kwargs)



def _get_merchandise_image_path(instance, filename):
	ext = filename.split('.')[-1].lower()
	filename = "%s.%s" % (uuid.uuid4(), ext)
	return os.path.join('img/user', str(instance.user.id), 'merchandise', filename)


class MerchandiseBase(models.Model):

	# 用户
	user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False)
	# 以下是物品关键资料，必填或者默认
	# --物品名称
	name = AlipaySubjectField(null=False, blank=False, editable=True)
	# --物品详细介绍
	description = models.TextField(max_length=400, help_text=u"简单介绍物品情况", default='', blank=True, editable=True)
	# --物品价格, range[0.01, 999999.99]
	price = AlipayPriceField(null=False, blank=False, editable=True) # 与支付宝物品价格保持一致(创建新modelfield)

	image = models.ImageField(upload_to=_get_merchandise_image_path, storage=storage, null=True, blank=True, editable=True)

	add_date = models.DateTimeField(auto_now_add=True, null=False, editable=True)

	# 附加物品信息 Metadata
	metadata = generic.GenericRelation(MetaData)

	# --CASCADE关联的post
	renren_posts = generic.GenericRelation('renren.RenrenPost',content_type_field='merchandise_type_id',
										   object_id_field='merchandise_id')
	weibo_posts = generic.GenericRelation('weibo.WeiboPost',content_type_field='merchandise_type_id',
										  object_id_field='merchandise_id')
	douban_posts = generic.GenericRelation('douban.DoubanPost',content_type_field='merchandise_type_id',
										   object_id_field='merchandise_id')

	class Meta:
		abstract = True
		unique_together = (('user', 'name'),)

	def delete(self):
		if self.image:
			if hasattr(settings, "AWS_SECRET_ACCESS_KEY"):
				image_path = urllib.unquote(self.image.name)
			else:
				image_path = self.image.path
			try:
				storage.delete(image_path)
			except Exception, err:
				logger.critical(u"%r delete %r fail ..." % (self, self.image))
		super(MerchandiseBase, self).delete()


class ItemManager(models.Manager):

	def get_unique_or_none(self, **kwargs):
		try:
			return self.get(**kwargs)
		except:
			return None

	def retrive_item(self, item, quantity):
		"""
		Thin wrapper around _decrement_item_availability
		"""
		return self._decrement_item_availability(item, quantity)

	def restore_item(self, item, quantity):
		"""
		Thin wrapper around _increment_item_availability
		"""
		return self._increment_item_availability(item, quantity)

	def _decrement_item_availability(self, item, quantity):
		"""
		Atomically decrease item availability
		Return True on success, False on fail
		"""

		status = False
		try:
			item.availability = models.F('availability') - quantity
			item.save(force_update=True)
			msg = u"物品获取成功"
		except Exception, err:
			logger.warning(u"decrease %r availability by %s fail，reason: %s" % (item, quantity, err))
			msg = u"物品数量不够"
			quantity = 0
		finally:
			# item reload
			item = self.get_unique_or_none(pk=item.pk)
			return (quantity, item, msg)

	def _increment_item_availability(self, item, quantity):
		"""
		Atomically increase item availability
		Return True on success, False on fail
		"""
		status = False

		try:
			item.availability = models.F('availability') + quantity
			item.save(force_update=True)
			status = True
		except Exception, err:
			logger.warning(u"增加%s可用数量%s失败，原因：%s" % (item, quantity, err))
			status = False
		finally:
			# item reload
			item = self.get_unique_or_none(pk=item.pk)
			return (status, item)





class Item(MerchandiseBase):
	"""
	仅仅作为Abstract Model,不能直接调用
	"""
	# --物品库存数量
	availability = models.PositiveIntegerField(null=False, blank=False, editable=True)
	# --每人物品购买上限, 购买上限最小为1,最大不限制
	purchase_limit = models.PositiveIntegerField(null=False, default=1, blank=True, editable=True, 
						validators=[MinValueValidator(1)])

	# 以下是不可编辑资料
	# --添加物品日期, 网站时间
	

	objects = ItemManager()


	class Meta(MerchandiseBase.Meta):
		abstract = True
		

	def __unicode__(self):
		return u"%s(%s)" % (self.name, self.pk)

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)


	def save(self, *args, **kwargs):
		if not self.purchase_limit:
			# 若用户没有设置每人最大购买上限，则上限默认为物品的availability, 不得小于1
			self.purchase_limit = self.availability if self.availability >= 1 else 1
		super(Item, self).save(*args, **kwargs)



	def get_absolute_url(self):
		"""
		"""
		raise NotImplementedError

	@property
	def number_sold(self):
		# TODO: cache it
		from dashboard.orders.models import Order
		self_type = ContentType.objects.get_for_model(self)
		return Order.objects.filter(merchandise_type__pk=self_type.pk, merchandise_id=self.pk).count()





class PhysicalItem(Item):
	
	# 物流方式, 与支付宝同步，如果虚拟物品默认为direct
	logistics_type = AlipayLogisticsTypeField(default='POST', null=True, blank=True, editable=True)
	# 物流价格
	logistics_fee = AlipayLogisticsFeeField(default=0, null=True, blank=True, editable=True)
	# 物流支付方式，与支付宝同步
	logistics_payment = AlipayLogisticsPaymentField(default='BUYER_PAY', null=False, editable=True)




	@property
	def show_url(self):
		"""
		必须在确保安全性前提下才能发出show_url
		"""
		return reverse('dashboard:listing:item-detail-physical', args=[str(self.pk)])


	def get_absolute_url(self):
		return reverse('dashboard:listing:item-update-physical', args=[str(self.pk)])








def _getDigitalFilePath(instance, filename):
	"""
	确保物品名称小于255
	"""
	logger.info(u"%r:%s:%s" % (_getDigitalFilePath, u'file name', filename))

	ext = filename.split('.')[-1].lower()
	filename = "%s.%s" % (uuid.uuid4(), ext)
	return os.path.join('digital_file/user', str(instance.user.id), 'item', filename)




class DigitalItem(Item):


	digital_file = DigitalItemFileField(max_length=255,
										upload_to=_getDigitalFilePath,
										max_upload_size=settings.MAX_DIGITAL_FILE_UPLOAD_SIZE, 
										content_types=settings.CONTENT_TYPES,
										null=False, blank=False, editable=True)



	def save(self, *args, **kwargs):
		super(DigitalItem, self).save(*args, **kwargs)

	@property
	def show_url(self):
		"""
		必须在确保安全性前提下才能发出show_url
		"""
		return reverse('dashboard:listing:item-detail-digital', args=[str(self.pk)])


	def get_absolute_url(self):
		return reverse('dashboard:listing:item-update-digital', args=[str(self.pk)])



	def generate_digitalfilepass(self, order, deliver_on_success=False, **kwargs):
		"""
		"""
		logger.info(u"%r creating digital file pass for %r...delivery?:%s" % (self, order.buyer, deliver_on_success))

		digital_file_pass = DigitalFilePass.objects.create_digitalfilepass(order=order,
																		owner=order.buyer,
																		digital_item=self,
																		deliver=deliver_on_success)
		return digital_file_pass






class EventItem(Item):
	"""
	Event item has default purchase limit to 1
	"""

	event_start = models.DateTimeField(null=False, blank=False, editable=True)
	time_zone = TimeZoneField(null=True, editable=True)

	

	def save(self, *args, **kwargs):
		"""
		WARNING: 自己设定event_start和event_end用来内部测试
		When pass in timezone unaware time, error could be thrown
		TODO
		"""
		if not djtimezone.is_aware(self.event_start):
			raise ValidationError(u"必须传入时区日期")

		event_start_tz = self.event_start.tzinfo

		self.purchase_limit = 1 # enforce purchase_limit to 1
		self.time_zone = event_start_tz

		super(EventItem, self).save(*args, **kwargs)


	@property
	def show_url(self):
		"""
		必须在确保安全性前提下才能发出show_url
		"""
		return reverse('dashboard:listing:item-detail-event', args=[str(self.pk)])




	def get_absolute_url(self):
		return reverse('dashboard:listing:item-update-event', args=[str(self.pk)])



	def generate_ticketpass(self, order, deliver_on_success=False, tz_support=True, **kwargs):
		"""
		返回创建的QR文件,失败返回None
		提醒：目前只支持门票
		不检查是否过期
		"""

		logger.info(u"%r creating ticket pass for %r ...delivery?:%s" % (self, order.buyer, deliver_on_success))

		if order.buyer_id == self.user_id:
			logger.critical("%s不能给自己的活动%s创建门票" % (order.buyer, self))
			return None

		#_now = djtimezone.now()
		
		#if _now >= self.expire_date:
		#	logger.critical("现在%s已经超过%r创建门票截至日期:%s(UTC)" % (_now, self, self.expire_date))
		#	return None


		ticket = TicketPass.objects.create_ticketpass(order=order, 
														owner=order.buyer, 
														event=self, 
														deliver=deliver_on_success)
		return ticket



	def get_event_attenders(self):
		"""
		查看活动的参加者
		"""
		tickets = TicketPass.objects.select_related('owner').filter(event_id=self.id)
		attenders = []
		for ticket in tickets:
			attenders.append(ticket.owner)
		return attenders








class Fund(MerchandiseBase):
	"""
	仅仅作为Abstract Model,不能直接调用
	"""
	# 筹资选填信息
	# --筹资照片, 微博图片大小需小于5M
	
	raised = models.PositiveIntegerField(default=0, null=False, editable=True)
	# --筹资目标，如果筹资目标设定，如果到达筹资目标通知用户
	goal = models.PositiveIntegerField(null=False, blank=False, editable=True) # we set a pre-defined soft upper limit



	class Meta(MerchandiseBase.Meta):
		abstract = True


	def __unicode__(self):
		return u"%s(%s)" % (self.name, self.pk)

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)


	def get_absolute_url(self):
		raise NotImplementedError

	@property
	def show_url(self):
		"""
		必须在确保安全性前提下才能发出show_url
		"""
		return reverse('dashboard:listing:fund-detail', args=[str(self.pk)])




class DonationFund(Fund):


	@property
	def show_url(self):
		"""
		必须在确保安全性前提下才能发出show_url
		"""
		return reverse('dashboard:listing:fund-detail-donation', args=[str(self.pk)])


	def get_absolute_url(self):
		return reverse('dashboard:listing:fund-update-donation', args=[str(self.pk)])	


class PaybackFund(Fund):

	@property
	def show_url(self):
		"""
		必须在确保安全性前提下才能发出show_url
		"""
		return reverse('dashboard:listing:fund-detail-payback', args=[str(self.pk)])

	def get_absolute_url(self):
		return reverse('dashboard:listing:fund-update-payback', args=[str(self.pk)])	



class DigitalFileSuperVisorManager(models.Manager):

	def clean_supervisors(self, hard_clean=False):
		"""
		clean supervisors that has digital_item set to null, and has no DigitalFilePass association, 
		or the file does not exist on the corresponding file_path
		"""
		
		supervisors = self.all()
		for supervisor in supervisors:
			if hard_clean: 
				supervisor.delete()
			else:
				if not supervisor.digital_file:
					from dashboard.passbook.models import DigitalFilePass
					reference_count = DigitalFilePass.objects.filter(digital_file_supervisor=supervisor).count()
					if reference_count < 1:
						supervisor.delete()


class DigitalFileSupervisor(models.Model):

	digital_item = models.ForeignKey('listing.DigitalItem', null=True, on_delete=models.SET_NULL, editable=False)
	digital_file = DigitalItemFileField(max_length=255,
										upload_to=_getDigitalFilePath,
										max_upload_size=settings.MAX_DIGITAL_FILE_UPLOAD_SIZE, 
										content_types=settings.CONTENT_TYPES,
										null=False, blank=False, editable=True)

	objects = DigitalFileSuperVisorManager()

	def __unicode__(self):
		return u"%s's digital file supervisor" % self.digital_item

	def __repr__(self):
		return u"%s(%s)" % (self.__class__.__name__, self.pk)


	def delete(self):
		"""
		"""
		#TODO: add remote storage support
		if hasattr(settings, "AWS_SECRET_ACCESS_KEY"):
			digital_file_path = urllib.unquote(self.digital_file.name)
		else:
			digital_file_path = self.digital_file.path
		try:
			storage.delete(digital_file_path)
		except Exception, err:
			logger.critical(u"%r delete %s fail, reason: %s" % (self, self.digital_file, err))
		super(DigitalFileSupervisor, self).delete()


	def get_digital_file_path(self):
		return self.digital_file.path

	def get_digital_file_absolute_url(self):
		return self.digital_file.url


@receiver(models.signals.post_save, sender=DigitalItem, weak=False, dispatch_uid='listing.signals.post_save_digitalitem')
def create_digitalfile_supervisor(sender, instance, created, *args, **kwargs):
	if created:
		digital_file_supervisor = DigitalFileSupervisor.objects.create(digital_item=instance, 
																		digital_file=instance.digital_file)



