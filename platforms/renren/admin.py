# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.contrib import admin

from platforms.renren.models import RenrenClient, RenrenPost


class RenrenPostInline(admin.StackedInline):
	model = RenrenPost
	fk_name = "client"
	readonly_fields = ('id','merchandise_type', 'merchandise_id', 'pid', 'uid', 'comment_count', 'client', 'post_type', 'view_count', 'share_count', )
	extra = 0

class RenrenClientAdmin(admin.ModelAdmin): 
	model = RenrenClient
	inlines = [RenrenPostInline, ]
	readonly_fields = ('id', 'user', 'uid', 'username', 'password', 'access_token', 'refresh_token', 'expires_in', 'visitor_count', 'friend_count', )



admin.site.register(RenrenClient, RenrenClientAdmin)



class RenrenPostAdmin(admin.ModelAdmin): 
	model = RenrenPost
	readonly_fields = ('id', 'merchandise_type', 'merchandise_id', 'pid', 'uid', 'comment_count', 'client', 'post_type', 'view_count', 'share_count', )


admin.site.register(RenrenPost, RenrenPostAdmin)