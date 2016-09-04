# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.utils import timezone as djtimezone
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView

import datetime

from dashboard.orders.mixin import PaymentStatMixin



class DashboardView(PaymentStatMixin, TemplateView):
	template_name = 'dashboard/index.html'
	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DashboardView, self).dispatch(*args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(DashboardView, self).get_context_data(**kwargs)

		# 以下用户界面内容将被缓存
		
		cache_key = 'dashboard.index.cache_key'
		cache_time = 60 # time to live in seconds, 10s in test base
		dashboard_data = cache.get(cache_key)

		if not dashboard_data:
			dashboard_data = {}
			dashboard_data = self.get_monthly_payment_stat(self.request.user)
			cache.set(cache_key, dashboard_data, cache_time)

		context['payment_stat'] = dashboard_data
		context['current_month'] = djtimezone.now().month
		context['current_year'] = djtimezone.now().year
		context['health_level'] = self.request.user.userhealthprofile.get_health_level_display()
		return context



