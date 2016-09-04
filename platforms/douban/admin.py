# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.contrib import admin

from models import DoubanClient, DoubanPost


class DoubanPostInline(admin.StackedInline):
	model = DoubanPost
	fk_name = "client"
	readonly_fields = ('id','merchandise_type', 'merchandise_id', 'pid', 'uid', 'comment_count', 'client', 'reshares_count', )
	extra = 0


class DoubanClientAdmin(admin.ModelAdmin): 
	model = DoubanClient
	readonly_fields = ('user', 'uid', 'access_token', 'username', 'password', 'refresh_token', 'expires_in', 'followers_count', 'following_count',)



admin.site.register(DoubanClient, DoubanClientAdmin)



class DoubanPostAdmin(admin.ModelAdmin): 
	model = DoubanPost
	readonly_fields = ('pid', 'uid', 'comment_count', 'priority', 'client', 'reshared_count', )


admin.site.register(DoubanPost, DoubanPostAdmin)
