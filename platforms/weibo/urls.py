# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


from django.conf.urls import patterns, url

import views

urlpatterns = patterns('', 
		url(r'^client_detail/(?P<pk>\d+)/$', views.WeiboClientDetailView.as_view(), name='client-detail'),		
		url(r'^oauth/$', views.WeiboClientOauthView.as_view(), name='oauth2'),
		url(r'^callback/$', views.WeiboClientCallbackView.as_view(), name='callback'),
		url(r'^client_delete/(?P<client_id>\d+)/$', views.delete_weiboclient, name='client-delete'),
)