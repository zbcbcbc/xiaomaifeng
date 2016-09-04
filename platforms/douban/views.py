# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang,Jian Chen"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging

from django.views.generic.detail import DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.db import IntegrityError
from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy

from platforms.views import *
from models import DoubanClient


logger = logging.getLogger('xiaomaifeng.platforms')


class DoubanClientOauthView(ClientOauthBaseView):
	"""
	普通用户只能连接一个微博帐号
	"""

	def get_redirect_url(self, **kwargs):
		#TODO cache url
		url = DoubanClient.objects.get_authorize_url()

		return url



class DoubanClientCallbackView(ClientCallbackBaseView):
	"""
	豆瓣认证Oauth2回调地址, 并创建WeiboClient
	"""

	def get_redirect_url(self, **kwargs):
		"""
		监测是否是从豆瓣返回值
		如果是，创立豆瓣帐户数据并且认为连接成功
		"""
		if self.request.GET.get('code'):
			code = self.request.GET['code'] #TODO 认证code
			# 创建或更新豆瓣用户
			status, r, msg = DoubanClient.objects.create_authorized_doubanclient(self.request.user, code, create_on_success=True)
			if status:
				messages.success(self.request, u'豆瓣用户连接成功', extra_tags='user-social-accounts')
			else:
				messages.warning(self.request, msg, extra_tags='user-social-accounts')

			return reverse('dashboard:profile:index')
		else:
			# GET 数据里没有code, raise http404
			raise Http404



class DoubanClientDetailView(ClientDetailBaseView):

	model = DoubanClient
	template_name = 'douban/doubanclient_detail.html'

	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		Cache client detail
		"""
		context = super(DoubanClientDetailView, self).get_context_data(**kwargs)
		client = context['client']
		#测试expires decorator用

		return context	



@login_required
def delete_doubanclient(request, client_id):
	"""
	A hack door to test timezone
	"""
	client = DoubanClient.objects.get(pk=client_id)
	client.delete()
	return HttpResponseRedirect(reverse('dashboard:profile:index'))



