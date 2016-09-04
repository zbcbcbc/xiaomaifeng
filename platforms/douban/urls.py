# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


from django.conf.urls import patterns, url

import views

urlpatterns = patterns('', 
		url(r'^client_detail/(?P<pk>\d+)/$', views.DoubanClientDetailView.as_view(), name='client-detail'),
		url(r'^oauth/$', views.DoubanClientOauthView.as_view(), name='oauth2'),
		url(r'^callback/$', views.DoubanClientCallbackView.as_view(), name='callback'),
		url(r'^client_delete/(?P<client_id>\d+)/$', views.delete_doubanclient, name='client-delete'),
)