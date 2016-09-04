# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from dashboard.profile.models import UserProfile, UserHealthProfile, UserGroup, Membership
from platforms.weibo.models import WeiboClient
from platforms.renren.models import RenrenClient
from platforms.douban.models import DoubanClient

# Define an inline admin descriptor for SiteUser model
# which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = u'用户资料'
    extra = 0
    max_num = 0

class UserHealthProfileInline(admin.StackedInline):
	model = UserHealthProfile
	can_delete = False
	verbose_name_plural = u'用户健康资料'
	extra = 0
	max_num = 0


class MembershipInline(admin.StackedInline):
	model = Membership

	can_delete = True
	verbose_name_plural = u'用户会员纪录'
	extra = 0
	max_num = 0


class WeiboClientInline(admin.StackedInline):
	model = WeiboClient
	can_delete = False
	verbose_name_plural = u'用户微博帐户'
	fields = ('id', 'user', 'uid', 'expires_in', )
	readonly_fields = ('id', 'user', 'uid', 'expires_in', )
	extra = 0
	max_num = 0

class RenrenClientInline(admin.StackedInline):
	model = RenrenClient
	can_delete = False
	verbose_name_plural = u'用户人人帐户'
	fields = ('id', 'user', 'uid', 'expires_in', )
	readonly_fields = ('id', 'user', 'uid', 'expires_in', )
	extra = 0
	max_num = 0

class DoubanClientInline(admin.StackedInline):
	model = DoubanClient
	can_delete = False
	verbose_name_plural = u'用户豆瓣帐户'
	fields = ('id', 'user', 'uid', 'expires_in', )
	readonly_fields = ('id', 'user', 'uid', 'expires_in', )
	extra = 0
	max_num = 0

# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, UserHealthProfileInline, MembershipInline, 
    			WeiboClientInline, RenrenClientInline, DoubanClientInline, )



class UserGroupAdmin(admin.ModelAdmin):
	pass

class UserProfileAdmin(admin.ModelAdmin):
	model = UserProfile

	#fields = ('user', 'address_1', 'address_2', 'province', 'country', 'zip_code', 
	#			'mobile', 'in_foreign', )
	readonly_fields = ('user', )
	#raw_id_fields = ('user',)

class UserHealthProfileAdmin(admin.ModelAdmin):
	model = UserHealthProfile

	raw_id_fields = ('user',)



# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserGroup, UserGroupAdmin)
admin.site.register(UserProfile, UserProfileAdmin)