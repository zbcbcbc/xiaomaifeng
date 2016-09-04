# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging

from django.views.generic.detail import DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from django.db import IntegrityError
from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy


from platforms.views import *
from models import WeiboClient

logger = logging.getLogger('xiaomaifeng.platforms')


class WeiboClientOauthView(ClientOauthBaseView):
	"""
	普通用户只能连接一个微博帐号
	"""

	def get_redirect_url(self, **kwargs):
		#TODO cache url
		url = WeiboClient.objects.get_authorize_url()

		return url



class WeiboClientCallbackView(ClientCallbackBaseView):
	"""
	微博认证Oauth2回调地址, 并创建WeiboClient
	"""

	def get_redirect_url(self, **kwargs):
		"""
		监测是否是从微博返回值
		如果是，创立微博帐户数据并且认为连接成功
		"""
		if self.request.GET.get('code'):
			code = self.request.GET['code'] #TODO 认证code
			# 创建或更新微博用户
			status, r, msg = WeiboClient.objects.create_authorized_weiboclient(self.request.user , code, create_on_success=True)
			if status:
				messages.success(self.request, u'微博用户连接成功', extra_tags='user-social-accounts')
			else:
				messages.warning(self.request, msg, extra_tags='user-social-accounts')

			return reverse('dashboard:profile:index')
		else:
			# GET 数据里没有code, raise http404
			raise Http404



class WeiboClientDetailView(ClientDetailBaseView):

	model = WeiboClient
	template_name = 'weibo/weiboclient_detail.html'

	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		Cache client detail
		"""
		context = super(WeiboClientDetailView, self).get_context_data(**kwargs)
		client = context['client']
		#测试expires decorator用

		return context	



@login_required
def delete_weiboclient(request, client_id):
	"""
	A hack door to test timezone
	"""
	client = WeiboClient.objects.get(pk=client_id)
	client.delete()
	return HttpResponseRedirect(reverse('dashboard:profile:index'))



