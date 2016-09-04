# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.contrib import admin

from platforms.alipay.models import AlipayClient



class AlipayClientAdmin(admin.ModelAdmin): 
	pass


admin.site.register(AlipayClient, AlipayClientAdmin)