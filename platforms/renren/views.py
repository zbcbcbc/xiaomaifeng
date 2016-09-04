# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


import logging

from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from django.db import IntegrityError
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages

from platforms.views import *
from models import RenrenClient


logger = logging.getLogger('xiaomaifeng.platforms')


class RenrenClientOauthView(ClientOauthBaseView):
	"""
	普通用户只能连接一个人人帐号
	"""

	def get_redirect_url(self, **kwargs):
		"""
		TODO: cache url
		"""
		url = RenrenClient.objects.get_authorize_url()
		return url



class RenrenClientCallbackView(ClientCallbackBaseView):
	"""
	人人Oauth2认证回调地址, 并创建RenrenClient
	"""

	def get_redirect_url(self, **kwargs):
		if self.request.GET.get('code'):
			#监测是否是从人人返回值, 如果是，创立人人帐户数据并且认为连接成功
			#TODO: verify code
			print self.request.GET
			code = self.request.GET.get('code', None)
			print 'code:', code

			status, r, msg = RenrenClient.objects.create_authorized_renrenclient(self.request.user, code, create_on_success=True)
			if status:
				messages.success(self.request, u'人人用户连接成功', extra_tags='user-social-accounts')
			else:
				messages.warning(self.request, msg, extra_tags='user-social-accounts')
				
			return reverse('dashboard:profile:index')

		else:
			print self.request
			print self.request.GET
			token = self.request.GET.get('token', None)
			print token
			return reverse('dashboard:profile:index')

		



class RenrenClientDetailView(ClientDetailBaseView):

	model = RenrenClient
	template_name = 'socialplatform/renren/renrenclient_detail.html'

	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		context = super(RenrenClientDetailView, self).get_context_data(**kwargs)
		return context



@login_required
def delete_renrenclient(request, client_id):
	"""
	A hack door to test timezone
	"""
	client = RenrenClient.objects.get(pk=client_id)
	client.delete()
	return HttpResponseRedirect(reverse('dashboard:profile:index'))












