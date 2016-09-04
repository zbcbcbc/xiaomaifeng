#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.conf.urls import patterns, url

from dashboard.profile import views

urlpatterns = patterns('', 
		url(r'^$', views.ProfileView.as_view(), name='index'),\
		url(r'^upgrade/$', views.UpgradeUserView.as_view(), name='user-upgrade'),
		url(r'^downgrade/$', views.DowngradeUserView.as_view(), name='user-downgrade'),
		url(r'^userprofile/$', views.UserProfileUpdateView.as_view(), name='userprofile-detail'),
)
