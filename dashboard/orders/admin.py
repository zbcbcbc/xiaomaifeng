# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.contrib import admin
from django.utils.translation import ugettext_lazy as _



from dashboard.orders.models import Order
from payment.alipay.models import AlipayPartnerTrade, AlipayDirectPay


class AlipayPartnerTradeInline(admin.StackedInline):
	model = AlipayPartnerTrade
	verbose_name_plural = _(u'支付宝货到付款')

	fk_name = 'xmf_order'
	readonly_fields = ('is_verified', 'token', 'body', 'trade_status', 'trade_no', 'gmt_create', 'logistics_type', 
						'logistics_fee', 'logistics_payment', 'gmt_logistics_modify', 
						'subject', 'quantity', 'price', 'payment_type', 'total_fee', 'discount', 
						'gmt_payment', 'use_coupon', 'seller_email', 'buyer_email', 'seller_alipay_id', 
						'buyer_alipay_id', 'receive_name', 'receive_address', 'receive_zip', 'receive_mobile',
						'gmt_refund', 'refund_status', 'logistics_name', 'invoice_no', 'transport_type', 
						'seller_ip', 'verify_url', 'it_b_pay', )
	extra = 0
	max_num = 0


class AlipayDirectPayInline(admin.StackedInline):
	model = AlipayDirectPay
	verbose_name_plural = _(u'支付宝及时到账')

	fk_name = 'xmf_order'
	readonly_fields = ('is_verified', 'body', 'token', 'trade_no', 'trade_status', 'gmt_create', 
						'gmt_close', 'payment_type', 'paymethod', 'total_fee', 'gmt_payment', 
						'seller_email', 'buyer_email', 'seller_alipay_id', 'buyer_alipay_id', 
						'subject', 'gmt_refund', 'refund_status', 'verify_url', )
	extra = 0
	max_num = 0


class OrderAdmin(admin.ModelAdmin):
	model = Order
	verbose_name_plural = _(u'订单')

	list_display = ('__unicode__', 'seller', 'buyer', 'merchandise_object', 'status', )

	inlines = [AlipayPartnerTradeInline, AlipayDirectPayInline]
	readonly_fields = ('id', 'seller', 'buyer', 'merchandise_object', 'payment_object', 
					'price', 'quantity', 'service_charge', 'logistics_fee', 
					'total_fee', 'payment_type', 'merchandise_id', 'payment_id', 'merchandise_type')
	search_fields = ['id']
	actions = ['cancel_order', 'resend_order_verification', ]



	def resend_order_verification(self, request, queryset):
		"""
		resend_order_verification only if order is not payment_verified
		"""
		for order in queryset:
			order.send_verification(created=False)

	resend_order_verification.short_description = _(u"重新发送交易认证")

admin.site.register(Order, OrderAdmin)


	
