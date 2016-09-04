# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang, JC"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from platforms.renren.models import RenrenClient, RenrenPost
from platforms.weibo.models import WeiboClient, WeiboPost
from platforms.douban.models import DoubanClient, DoubanPost


logger = logging.getLogger('site.platforms')


class MerchandiseToSocialClientsMixin(object):
	"""
	物品和Social Client 的mixin
	"""

	def upload_to_social_clients(self, request, merchandise, client_form):
		"""
		尝试添加merchandise 到 social client帐户
		"""
		user = request.user # 在这里缓存用户

		renren_client_select = client_form.cleaned_data.get('renren_client', False) # return is a list and always one selected only
		if renren_client_select:
			# 用户选择人人帐户id, 找出对应人人帐户
			client = RenrenClient.objects.get_unique_or_none(user=user)
			if client:
				aid = client_form.cleaned_data.get('renren_choices', None)
				message = client_form.cleaned_data.get('renren_message', None)
				if aid and aid == 'status': #TODO: bug
					"""
					发布到人人状态
					"""
					# this is a status post, no image upload
					status, _, msg = client.create_post(merchandise, message=message)
					if status:
						messages.success(self.request, msg, extra_tags=getattr(self, 'msg_tags', None))
					else:
						messages.warning(self.request, msg, extra_tags=getattr(self, 'msg_tags', None))
				else:
					"""
					发布到人人相册
					"""
					# this is a photo post, but check if the item has image
					if merchandise.image:
						status, _, msg = client.create_photo_post(merchandise, aid, message=message)
						if status:
							messages.success(self.request, msg, extra_tags=getattr(self, 'msg_tags', None))
						else:
							messages.warning(self.request, msg, extra_tags=getattr(self, 'msg_tags', None))
					else:
						# this item has no image, so don't post it!
						messages.warning(self.request, u'这件物品没有照片，无法上传到人人照片', extra_tags=getattr(self, 'msg_tags', None))
						logger.warning(u"%s:%s" % (getattr(self, 'TAG', None), u'这件物品没有照片，无法上传到人人相册'))
			else:
				# 用户选择的人人帐户不存在数据库
				messages.warning(self.request, u'用户选择的人人帐户不存在数据库', extra_tags=getattr(self, 'msg_tags', None))		
				logger.error(u"%s:%s" % (getattr(self, 'TAG', None), u'用户%s选择的人人帐户不存在数据库' % (user)))			
		else:
			# 用户没有选择人人帐户，忽略
			pass

		"""
		添加物品到关联的豆瓣帐户，如果物品有照片则默认为豆瓣照片上传，若没有照片则默认为普通豆瓣广播上传
		"""
		douban_client_select = client_form.cleaned_data.get('douban_client', False)
		if douban_client_select:
			client = DoubanClient.objects.get_unique_or_none(user=user)
			if client:
				message = client_form.cleaned_data.get('douban_message', None)
				status, _, msg = client.create_post(merchandise, message=message)
				if status:
					messages.success(self.request, msg, extra_tags=getattr(self, 'msg_tags', None))
				else:
					messages.warning(self.request, msg, extra_tags=getattr(self, 'msg_tags', None))
			else:
				# 用户选择的豆瓣帐户不存在数据库
				messages.warning(self.request, u'用户选择的豆瓣帐户不存在数据库', extra_tags=getattr(self, 'msg_tags', None))
				logger.error(u"%s:%s" % (getattr(self, 'TAG', None), u'用户%s选择的豆瓣帐户不存在数据库' % (user)))
		else:
			# 用户没有选择豆瓣帐户，忽略
			logger.info(u"%s:%s" % (getattr(self, 'TAG', None), u'用户%s没有选择豆瓣帐户，忽略' % (user)))
			pass

		"""
		添加物品到关联的微博帐户，如果物品有照片则默认为微博照片上传，若没有照片则默认为普通微博上传
		"""
		weibo_client_select = client_form.cleaned_data.get('weibo_client', False)
		if weibo_client_select:
			client = WeiboClient.objects.get_unique_or_none(user=user)
			if client:
				message = client_form.cleaned_data.get('weibo_message', None)
				status, _, msg = client.create_post(merchandise, message=message)
				if status:
					messages.success(self.request, msg, extra_tags=getattr(self, 'msg_tags', None))
				else:
					messages.warning(self.request, msg, extra_tags=getattr(self, 'msg_tags', None))
			else:
				# 用户选择的微博帐户不存在数据库
				messages.warning(self.request, u'用户选择的微博帐户不存在数据库', extra_tags=getattr(self, 'msg_tags', None))
				logger.error(u"%s:%s" % (getattr(self, 'TAG', None), u'用户%s选择的微博帐户不存在数据库' % (user)))
		else:
			# 用户没有选择微博帐户，忽略
			logger.info(u"%s:%s" % (getattr(self, 'TAG', None), u'用户%s没有选择微博帐户，忽略' % (user)))
			pass



	def update_merchandise_posts(self, merchandise):
		"""
		返回与物品相关的post列表，不扔出错误，如果出现错误则返回空列表
		"""
		logger.info(u"%s:%s" % (getattr(self, 'TAG', None), u'更新与物品相关的Post中...'))


		merchandise_posts = []
		merchandise_type = ContentType.objects.get_for_model(merchandise)
		weibo_post = WeiboPost.objects.select_related('client').filter(merchandise_type__pk=merchandise_type.id, merchandise_id=merchandise.pk)
		renren_post = RenrenPost.objects.select_related('client').filter(merchandise_type__pk=merchandise_type.id, merchandise_id=merchandise.pk)
		douban_post = DoubanPost.objects.select_related('client').filter(merchandise_type__pk=merchandise_type.id, merchandise_id=merchandise.pk)

		for post in weibo_post:
			client = post.client
			status, _, msg = client.update_post(post)
			if status:
				merchandise_posts.append({'id':post.id,'user_name':post.client.user_name, 'platform':post.client.social_platform.verbose_name,
						'text':post.text, 'post_date':post.post_date, 'comments_count':post.comment_count})
		for post in renren_post:
			client = post.client
			status, _, msg = client.update_post(post)
			if status:
				merchandise_posts.append({'id':post.id, 'user_name':post.client.user_name, 'platform':post.client.social_platform.verbose_name,
					'text':post.text, 'post_date':post.post_date, 'comments_count':post.comment_count})
		
		for post in douban_post:
			client = post.client
			status, _, msg = client.update_post(post)
			if status:
				merchandise_posts.append({'id':post.id,'user_name':post.client.user_name, 'platform':post.client.social_platform.verbose_name,
					'text':post.text, 'post_date':post.post_date, 'comments_count':post.comment_count})

		return merchandise_posts





