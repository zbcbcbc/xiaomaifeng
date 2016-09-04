# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import time, logging

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy

from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, FormView
from django.views.generic.base import TemplateView, RedirectView



from forms import UserProfileForm, UpgradeUserForm
from models import UserProfile, Membership



logger = logging.getLogger('xiaomaifeng.profile')



class UpgradeUserView(FormView):

	template_name = 'profile/upgrade_user.html'
	form_class = UpgradeUserForm
	success_url = reverse_lazy('dashboard:profile:index')
	http_method_names = ['get', 'post', 'head', 'options', 'trace']
	

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		raise Http404
		self.msg_tags = 'user-profile'
		return super(UpgradeUserView, self).dispatch(*args, **kwargs)

	def form_valid(self, form):
		
		group = form.cleaned_data['user_group']

		# 尝试升级用户
		status, msg = Membership.objects.upgrade_user(user=self.request.user, group=group)

		if status:
			messages.success(self.request, msg, extra_tags=self.msg_tags)
		else:
			messages.warning(self.request, msg, extra_tags=self.msg_tags)

		return super(UpgradeUserView, self).form_valid(form)




class DowngradeUserView(RedirectView):
	"""
	仅仅用于测试用户upgrade
	"""
	permanent = False # used for testing, change to True for production

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		self.TAG = 'DowngradeUserView'
		self.msg_tags = 'user-profile'
		return super(DowngradeUserView, self).dispatch(*args, **kwargs)

	def get_redirect_url(self, **kwargs):

		# 尝试降级用户
		status, msg = Membership.objects.downgrade_user(self.request.user)

		return reverse('dashboard:profile:index')




class ProfileView(TemplateView):
	"""
	这里经常用来做method 测试
	"""

	template_name = "profile/index.html"

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		self.TAG = 'ProfileView'
		self.msg_tags = 'user-profile'
		return super(ProfileView, self).dispatch(*args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(ProfileView, self).get_context_data(**kwargs)

		try:
			context['renren_client'] = self.request.user.renrenclient
		except Exception, err:
			print err
			pass

		try:
			context['weibo_client'] = self.request.user.weiboclient
		except:
			pass

		try:
			context['alipay_client'] = self.request.user.alipayclient
		except:
			pass

		try:
			context['douban_client'] = self.request.user.doubanclient
		except:
			pass


		return context





class UserProfileUpdateView(UpdateView):
	form_class = UserProfileForm
	model = UserProfile
	template_name = 'profile/userprofile_detail.html'
	context_object_name = "userprofile"
	success_url = reverse_lazy('dashboard:profile:userprofile-detail')
	http_method_names = ['get', 'post', 'head', 'options', 'trace']


	# under development

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		self.TAG = 'UserProfileUpdateView'
		self.msg_tags = 'user-profile'
		return super(UserProfileUpdateView, self).dispatch(*args, **kwargs)
		

	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		context = super(UserProfileUpdateView, self).get_context_data(**kwargs)
		context['username'] = self.request.user.username
		return context

	def get_object(self, queryset=None):
		"""
		override default get_object method
		"""
		userprofile = UserProfile.objects.get(pk=self.request.user)
		return userprofile


	def form_invalid(self, form):
		messages.warning(self.request, u'更新失败', extra_tags=self.msg_tags)
		logger.info(u"%s:%s" % (self.TAG, u"用户%r帐户更新表格填写错误" % (self.request.user)))
		return super(UserProfileUpdateView, self).form_invalid(form)

	def form_valid(self, form):
		messages.success(self.request, u'更新成功', extra_tags=self.msg_tags)
		logger.info(u"%s:%s" % (self.TAG, u"用户%s帐户更新成功" % (self.request.user)))
		return super(UserProfileUpdateView, self).form_valid(form)



		









