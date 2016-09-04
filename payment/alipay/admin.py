# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from django.contrib import admin

from payment.admin import PartnerTradeBaseAdmin, DirectPayBaseAdmin
from payment.alipay.models import AlipayPartnerTrade, AlipayDirectPay


class AlipayPartnerTradeAdmin(PartnerTradeBaseAdmin):
	model = AlipayPartnerTrade
	list_display = ('__unicode__','xmf_order', 'is_verified', 'trade_status', )
	readonly_fields = ('token', 'body', 'trade_status', 'trade_no', 'gmt_create', 'logistics_type', 
						'logistics_fee', 'logistics_payment', 'gmt_logistics_modify', 
						'subject', 'quantity', 'price', 'payment_type', 'total_fee', 'discount', 
						'gmt_payment', 'use_coupon', 'seller_email', 'buyer_email', 'seller_alipay_id', 
						'buyer_alipay_id', 'receive_name', 'receive_address', 'receive_zip', 'receive_mobile',
						'gmt_refund', 'refund_status', 'logistics_name', 'invoice_no', 'transport_type', 
						'seller_ip', 'it_b_pay', )

admin.site.register(AlipayPartnerTrade, AlipayPartnerTradeAdmin)



class AlipayDirectPayAdmin(DirectPayBaseAdmin):
	model = AlipayDirectPay
	list_display = ('__unicode__', 'is_verified', 'trade_status', )
	readonly_fields = ('body', 'token', 'trade_no', 'trade_status', 'gmt_create', 
						'gmt_close', 'payment_type', 'paymethod', 'total_fee', 'gmt_payment', 
						'seller_email', 'buyer_email', 'seller_alipay_id', 'buyer_alipay_id', 
						'subject', 'gmt_refund', 'refund_status', 'verify_url', )

admin.site.register(AlipayDirectPay, AlipayDirectPayAdmin)