# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    #TODO: hash urls to make them less recognizable

	url(r'^oauth2/$', views.AlipayClientOauthView.as_view(), name='oauth2'),
	url(r'^callback/$', views.AlipayClientCallbackView.as_view(), name='callback'),
	url(r'^client_detail/(?P<pk>\d+)/$', views.AlipayClientDetailView.as_view(), name='client-detail'),
)