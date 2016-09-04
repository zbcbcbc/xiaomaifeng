# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView



class ClientOauthBaseView(RedirectView):

	permanent = False # used for testing, change to True for production

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ClientOauthBaseView, self).dispatch(*args, **kwargs)


	def get_redirect_url(self, **kwargs):
		raise NotImplementedError



class ClientCallbackBaseView(RedirectView):

	permanent = False # used for testing, change to True for production

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ClientCallbackBaseView, self).dispatch(*args, **kwargs)

	def get_redirect_url(self, **kwargs):
		"""
		在这里创建SocialClient
		"""
		raise NotImplementedError



class ClientDetailBaseView(DetailView):

	context_object_name = "client"
	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ClientDetailBaseView, self).dispatch(*args, **kwargs)	






