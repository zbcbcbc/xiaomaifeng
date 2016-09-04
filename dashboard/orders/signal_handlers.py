# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging

from django.core.urlresolvers import reverse

from notification import models as notification
from dashboard.listing.models import PhysicalItem, EventItem, DigitalItem, DonationFund, PaybackFund
from payment.models import PartnerTradeBaseModel, DirectPayBaseModel
from metadata.models import MetaData
from modelfields import OrderStatus


logger = logging.getLogger('xiaomaifeng.orders')



# 支付宝担保交易下单成功Handler
def create_order_success_handler(sender, order, payment, **kwargs):
	"""
	交易数据后，更新认证Url,并且发送给买家认证url执行认证，不通知卖家
	"""

	# Alipay Partner Trade Order 第一次建立
	# 获取verify url 并保存
	# TODO: use urllib open to verify automatically

	logger.info(u"%r sending verify email to %r..." % (order, order.buyer))
	
	try:
		merchandise = order.merchandise_object
		metadatas = MetaData.objects.get_content_metadata(merchandise)
		#TODO: use temporarory url for now
		#TODO: add security (secert key)
		if isinstance(merchandise, PhysicalItem):
			notification.send([order.buyer], "order_verify_physicalitem", {
							"merchandise":merchandise,
							"metadatas":metadatas,
							"order":order,
							"payment":payment})

		elif isinstance(merchandise, DigitalItem):
			 notification.send([order.buyer], "order_verify_digitalitem", {
							"merchandise":merchandise,
							"metadatas":metadatas,
							"order":order,
							"payment":payment})

		elif isinstance(merchandise, EventItem):
			 notification.send([order.buyer], "order_verify_eventitem", {
							"merchandise":merchandise,
							"metadatas":metadatas,
							"order":order,
							"payment":payment})   

		elif isinstance(merchandise, PaybackFund):
			 notification.send([order.buyer], "order_verify_paybackfund", {
							"merchandise":merchandise,
							"metadatas":metadatas,
							"order":order,
							"payment":payment})

		elif isinstance(merchandise, DonationFund):
			 notification.send([order.buyer], "order_verify_donationfund", {
							"merchandise":merchandise,
							"metadatas":metadatas,
							"order":order,
							"payment":payment})

	except Exception, err:
		logger.critical(u"%r send verify emailt to %r fail, reason: %s" % (order, order.buyer, err))
		pass


def create_order_fail_handler(sender, buyer, title, comment, social_platform, quantity, reason, **kwargs):
	"""
	交易建立失败，获取失败原因并发送给买家
	传入参数kwargs:{"payer","body","comment","social_platform","quantity","reason"}
	"""
	
	logger.info(u"发送交易建立失败邮件给%r..." % (buyer))    

	try:
		notification.send([buyer], "create_order_fail", {"reason":reason, 
								"title":title,
								"comment":comment,
								"social_platform":social_platform,
								"quantity":quantity})
	except Exception, err:
		logger.error(u"发送交易建立失败邮件给%r失败，原因: %s" % (buyer, err))
		pass



def order_payment_verify_success_handler(sender, payment, **kwargs):
	"""
	买家支付宝担保交易认证成功逻辑:
		通知卖家寄货(send_goods_url)，并且告知买家已认证，等待寄货中
		如果是虚拟物品则发送或者创建对应二维码然后发送给买家，并且自动确认发货
	传入kwargs{'instance', }
	#TODO: If either one sent fail, resend
	#TODO: Queue notification
	"""
	logger.info(u'receive from %r payment verify success signal..' % (payment))


	try:
		#print 'payment_verified:', payment.is_verified
		if not payment.is_verified:
			raise Exception('payment unverified sending wrong signal...')

		order = payment.xmf_order

		#print 'order expired:', order.is_expired
		if order.is_expired:
			raise Exception('%r has expired...' % order)

		#print 'order finished:', order.is_finished
		if order.is_finished:
			raise Exception('%r is finished...' % order)


		merchandise = order.merchandise_object # 缓存物品
		base_ctx = {"order":order, "payment":payment, "merchandise":merchandise}

		if isinstance(payment, PartnerTradeBaseModel):
			# update order status
			order.status = OrderStatus.PAYMENT_VERIFIED
			order.save(force_update=True)

			if isinstance(merchandise, EventItem):
				# 如果是虚拟物品, 并且可以创建门票，则创建门票并发送
				ticket_pass = merchandise.generate_ticketpass(order, deliver_on_success=False)
				# 确认发货
				payment.shippment_confirm()

				# initiate event context
				event_ctx = {}
				event_ctx.update(base_ctx)

				# initiate event_buyer context
				event_buyer_ctx = {}
				event_buyer_ctx.update(event_ctx)
				event_buyer_ctx['ticket_pass'] = ticket_pass
				event_buyer_ctx['role'] = 'buyer'

				logger.info(u"%r sending payment verify success email to %r..." % (order, order.buyer))
				notification.send([order.buyer], "order_verify_success_eventitem", event_buyer_ctx)

				# initiate digital seller context
				event_seller_ctx = {}
				event_seller_ctx.update(event_ctx)	
				event_seller_ctx['role'] = 'seller'			

				logger.info(u'%r sending payment verify success email to %r...' % (order, order.seller))
				notification.send([order.seller], "order_verify_success_eventitem", event_seller_ctx) #STUB: instance.send_goods_confirmation()

			elif isinstance(merchandise, DigitalItem):
				# 虚拟物品，发送虚拟物品连接给买家，提供下载 (TODO: pdf content provider)
				digital_file_pass = merchandise.generate_digitalfilepass(order, deliver_on_success=False)
				# shippment confirm
				payment.shippment_confirm()
				# initiate digital context
				digital_ctx = {}
				digital_ctx.update(base_ctx)
				# initiate digital buyer context
				digital_buyer_ctx = {}
				digital_buyer_ctx.update(digital_ctx)
				digital_buyer_ctx['digital_file_pass'] = digital_file_pass
				digital_buyer_ctx['role'] = 'buyer'

				logger.info(u"%r sending payment verify success email to buyer: %r..." % (order, order.buyer))
				notification.send([order.buyer], "order_verify_success_digitalitem", digital_buyer_ctx)

				# initiate digital seller context
				digital_seller_ctx = {}
				digital_seller_ctx.update(digital_ctx)
				digital_seller_ctx['role'] = 'seller'			

				logger.info(u'%r sending payment verify success email to seller: %r...' % (order, order.seller))
				notification.send([order.seller], "order_verify_success_digitalitem", digital_seller_ctx) #STUB: instance.send_goods_confirmation()

			elif isinstance(merchandise, PhysicalItem):
				# 实体物品，不发送物品，发送邮件给卖家

				# initiate physical context
				physical_ctx = {}
				physical_ctx.update(base_ctx)

				# initiate physical buyer context
				physical_buyer_ctx = {}
				physical_buyer_ctx.update(physical_ctx)
				physical_buyer_ctx['role'] = 'buyer'

				logger.info(u"%r sending payment verify success email to %r..." % (order, order.buyer))
				notification.send([order.buyer], "order_verify_success_physicalitem", physical_buyer_ctx)

			
				# TODO
				# url = instance.send_goods_confirmation(auto_send=False)

				# initiate physical seller context
				physical_seller_ctx = {}
				physical_seller_ctx.update(physical_ctx)
				physical_seller_ctx['send_good_url'] = u'请点击这里确认寄货'
				physical_seller_ctx['role'] = 'seller'

				logger.info(u'%r sending payment verify success email to seller: %r...' % (order, order.seller))
				notification.send([order.seller], "order_verify_success_physicalitem", physical_seller_ctx) #STUB: instance.send_goods_confirmation()
			else:
				raise Exception("Merchandise type is: %s" % merchandise.__class__)

		elif isinstance(payment, DirectPayBaseModel):
			# update order status
			order.set_succeed()

			if isinstance(merchandise, PaybackFund):
				# initiate payback context
				payback_ctx = {}
				payback_ctx.update(base_ctx)

				# initiate payback buyer context
				payback_buyer_ctx = {}
				payback_buyer_ctx.update(payback_ctx)
				payback_buyer_ctx['role'] = 'buyer'

				logger.info(u"%r sending payment verify success email to %r..." % (order, order.buyer))
				notification.send([order.buyer], "order_verify_success_paybackfund", payback_buyer_ctx)

				# initiate payback seller context
				payback_seller_ctx = {}
				payback_seller_ctx.update(payback_ctx)
				payback_seller_ctx['role'] = 'seller'
				logger.info(u'%r sending payment verify success email to %r...' % (order, order.seller))
				notification.send([order.seller], "order_verify_success_paybackfund", payback_seller_ctx) #STUB: instance.send_goods_confirmation()

			elif isinstance(merchandise, DonationFund):
				# initiate donation context
				donation_ctx = {}
				donation_ctx.update(base_ctx)

				# initiate donation buyer context
				donation_buyer_ctx = {}
				donation_buyer_ctx.update(donation_ctx)
				donation_buyer_ctx['role'] = 'buyer'

				logger.info(u"%r sending payment verify success email to buyer: %r..." % (order, order.buyer))
				notification.send([order.buyer], "order_verify_success_donationfund", donation_buyer_ctx)

				# initiate donation seller context
				donation_seller_ctx = {}
				donation_seller_ctx.update(donation_ctx)
				donation_seller_ctx['role'] = 'seller'

				logger.info(u'%r sending payment verify success email to seller: %r...' % (order, order.seller))
				notification.send([order.seller], "order_verify_success_donationfund", donation_seller_ctx) #STUB: instance.send_goods_confirmation()

		else:
			raise Exception("Payment type is: %s" % payment.__class__)

	except Exception, err:
		logger.critical(u"%r payment verify success handler fail, reason: %s" % (order, order.buyer, err))     
		pass


def order_shippment_confirm_success_handler(sender, payment, **kwargs):
	"""
	"""
	logger.info(u'receive from %r shippment confirm success signal..' % (payment))

	try:
		order = payment.xmf_order
		merchandise = order.merchandise_object
		base_ctx = {"order":order, "payment":payment, "merchandise":merchandise}

		if not payment.is_verified:
			raise Exception('payment unverified sending wrong signal...')

		if order.is_expired:
			raise Exception('%r has expired...' % order)

		if order.is_finished:
			raise Exception('%r is finished...' % order)
		
		order.status = OrderStatus.SHIPPMENT_CONFIRMMED
		order.save(force_update=True)

		if isinstance(merchandise, PhysicalItem):
			# initiate physical context
			physical_ctx = {}
			physical_ctx.update(base_ctx)

			# initiate physical buyer context
			physical_buyer_ctx = {}
			physical_buyer_ctx.update(physical_ctx)
			physical_buyer_ctx['role'] = 'buyer'

			logger.info(u"%r sending shippment confirmed success email to buyer: %r..." % (order, order.buyer))
			notification.send([order.buyer], "order_shippment_confirmed_physicalitem", physical_buyer_ctx)

		else:
			pass

	except Exception, err:
		logger.critical(u"order shippment confirm success handler err:%s " % err)





