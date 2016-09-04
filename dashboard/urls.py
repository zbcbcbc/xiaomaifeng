# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.conf.urls import patterns, include, url

import views

urlpatterns = patterns('', 
		url(r'^$', views.DashboardView.as_view(), name='index'),
		url(r'^orders/', include('dashboard.orders.urls', namespace='orders')),
		url(r'^profile/', include('dashboard.profile.urls', namespace='profile')),
		url(r'^listing/', include('dashboard.listing.urls', namespace='listing')),
		url(r'^passbook/', include('dashboard.passbook.urls', namespace='passbook')),
)
