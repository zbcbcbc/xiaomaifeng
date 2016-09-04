# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.contrib import admin

from platforms.weibo.models import WeiboClient, WeiboPost



class WeiboPostInline(admin.StackedInline):
	model = WeiboPost
	fk_name = "client"
	readonly_fields = ('id','merchandise_type', 'merchandise_id', 'pid', 'uid', 'comment_count', 'client', 'reposts_count')
	extra = 0


class WeiboClientAdmin(admin.ModelAdmin): 
	model = WeiboClient
	inlines = [WeiboPostInline, ]
	readonly_fields = ('id', 'user', 'uid', 'username', 'password', 'access_token', 'refresh_token', 'expires_in', 'followers_count', 'friends_count',)


admin.site.register(WeiboClient, WeiboClientAdmin)



class WeiboPostAdmin(admin.ModelAdmin): 
	model = WeiboPost
	search_fields = ['id', 'client__id', ]
	readonly_fields = ('id','merchandise_type', 'merchandise_id', 'pid', 'uid', 'comment_count', 'client', 'reposts_count')


admin.site.register(WeiboPost, WeiboPostAdmin)
