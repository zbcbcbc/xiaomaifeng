# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import datetime
import logging

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages

from platforms.views import *
from models import AlipayClient


logger = logging.getLogger('xiaomaifeng.platforms')

ALIPAY_CALLBACK_URL = reverse_lazy('platforms:alipay:callback')


class AlipayClientOauthView(ClientOauthBaseView):
	"""
	普通用户只能连接一个支付宝帐号
	"""

	def get_redirect_url(self, **kwargs):
		try:
			redirect_uri = ALIPAY_CALLBACK_URL
			url = AlipayClient.get_authorize_url(redirect_uri)
			return ALIPAY_CALLBACK_URL
		except Exception, err:
			print err
			return reverse('dashboard:profile:index')


class AlipayClientCallbackView(ClientCallbackBaseView):


	def get_redirect_url(self, **kwargs):
		if self.request.GET.get('code'):
			print self.request.GET['code']
			#TODO: 创建AlipayClient
			messagess.success(self.request, u'连接支付宝成功', extra_tags='user-banking')
		else:
			print 'fake redirect result'
		return reverse('dashboard:profile:index')




class AlipayClientDetailView(ClientDetailBaseView):
	model = AlipayClient
	template_name = 'platforms/alipay/alipayclient_detail.html'

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(AlipayClientDetailView, self).dispatch(*args, **kwargs)

	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		context = super(AlipayClientDetailView, self).get_context_data(**kwargs)
		return context















