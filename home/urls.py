# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.conf.urls import patterns, url

from home import views

urlpatterns = patterns('',
		url(r'^$', views.HomeView.as_view(), name='index'),
		url(r'^term/$', views.TermView.as_view(), name='term'),
		url(r'^privacy/$', views.PrivacyView.as_view(), name='privacy'),
)
