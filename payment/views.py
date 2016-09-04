# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView




class DirectPayDetailBaseView(DetailView):

	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DirectPayDetailBaseView, self).dispatch(*args, **kwargs)


	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		return super(DirectPayDetailBaseView, self).get_context_data(**kwargs)



class PartnerTradeVerifyBaseView(RedirectView):
	"""
	用户按认证连接后的页面，如果Order存在，未认证过并且没有过期，
	则引导用户到相对应支付页面，否则返回错误信息
	注: 测试用，或者可以作为安全连接
	"""

	permanent = False


	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(PartnerTradeVerifyBaseView, self).dispatch(*args, **kwargs)
		

	def get_redirect_url(self, **kwargs):
		"""
		WARNING: THIS METHOD SHOULD BE OVERRIDE
		"""
		raise NotImplementedError # WARNING: override this method


class DirectPayVerifyBaseView(RedirectView):
	"""
	用户按认证连接后的页面，如果Order存在，未认证过并且没有过期，
	则引导用户到相对应支付页面，否则返回错误信息
	注: 测试用，或者可以作为安全连接
	"""

	permanent = False

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DirectPayVerifyBaseView, self).dispatch(*args, **kwargs)

	def get_redirect_url(self, **kwargs):
		"""
		WARNING: THIS METHOD SHOULD BE OVERRIDE
		"""
		raise NotImplementedError

