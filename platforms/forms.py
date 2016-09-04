# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang, JC"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from platforms.renren.models import RenrenClient, RenrenPost
from platforms.weibo.models import WeiboClient, WeiboPost
from platforms.douban.models import DoubanClient, DoubanPost


class SelectSocialClientForm(forms.Form):
	"""
	限制普通用户在一个社交帐户上同时post2件或2件以上同一件物品
	返回最新人人相册列表
	"""
	def __init__(self, *args, **kwargs):

		user = kwargs.pop('user')
		content = kwargs.pop('content', None)
		super(SelectSocialClientForm, self).__init__(*args, **kwargs)


		if content:
			content_type = ContentType.objects.get_for_model(content)
		else:
			content_type = None

		renren_client = RenrenClient.objects.get_unique_or_none(user=user)
		if renren_client:
			#检查物品是否已经在人人上post过
			if content_type and content:
				used_count = RenrenPost.objects.filter(client=renren_client, merchandise_type__pk=content_type.id, merchandise_id=content.id).count()
				if used_count > 0:
					#普通用户只能在人人上post一次
					renren_client = None
			else:
				# 这件物品第一次被post
				pass

		weibo_client = WeiboClient.objects.get_unique_or_none(user=user)
		if weibo_client:
			#检查物品是否已经在微博上post过
			if content_type and content:
				used_count = WeiboPost.objects.filter(client=weibo_client, merchandise_type__pk=content_type.id, merchandise_id=content.id).count()
				#普通用户只能在微博上post一次
				if used_count > 0:
					weibo_client = None
			else:
				# 这件物品第一次被post
				pass

		douban_client = DoubanClient.objects.get_unique_or_none(user=user)
		if douban_client:
			#检查物品是否已经在豆瓣上post过
			if content_type and content:
				used_count = DoubanPost.objects.filter(client=douban_client, merchandise_type__pk=content_type.id, merchandise_id=content.id).count()
				#普通用户只能在豆瓣上post一次
				if used_count > 0:
					douban_client = None
			else:
				# 这件物品第一次被post
				pass

		if renren_client:
			status, albums, msg = renren_client.get_album_list()
			renren_status_choices = (('status', u'状态'),)
			if status:
				# 相册列表获取成功
				renren_album_choices = ((album['id'], album['name']) for album in albums)
				renren_choices =  renren_status_choices + tuple(renren_album_choices)
			else:
				renren_choices = renren_status_choices

			self.fields['renren_client'] = forms.BooleanField(required=False, label=u"%s:%s" %(u'人人帐户', renren_client.user_name)) 
			self.fields['renren_choices'] = forms.ChoiceField(choices=renren_choices, label=u'添加到', initial='renren_status')
			self.fields['renren_message'] = forms.CharField(max_length=100, required=False, widget=forms.Textarea, label=u'描述')
		
		if weibo_client:
			self.fields['weibo_client'] = forms.BooleanField(required=False, label=u"%s:%s" %(u'微博帐户', weibo_client.user_name))
			self.fields['weibo_message'] = forms.CharField(max_length=100, required=False, widget=forms.Textarea, label=u'微博')

		if douban_client:
			self.fields['douban_client'] = forms.BooleanField(required=False, label=u"%s:%s" %(u'豆瓣帐户', douban_client.user_name))
			self.fields['douban_message'] = forms.CharField(max_length=100, required=False, widget=forms.Textarea, label=u'豆瓣')
