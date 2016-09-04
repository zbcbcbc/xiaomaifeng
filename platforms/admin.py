# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.contrib import admin

from platforms.models import SocialPlatform



class SocialPlatformAdmin(admin.ModelAdmin): 
	model = SocialPlatform


admin.site.register(SocialPlatform, SocialPlatformAdmin)