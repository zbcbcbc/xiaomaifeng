# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.contrib import admin



class PaymentBaseAdmin(admin.ModelAdmin): 
	readonly_fields = ('xmf_order', 'is_verified', )


class PartnerTradeBaseAdmin(admin.ModelAdmin):
	pass


class DirectPayBaseAdmin(admin.ModelAdmin):
	pass