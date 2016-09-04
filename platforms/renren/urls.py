# -*- coding: utf-8 -*-
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('', 
		url(r'^client_detail/(?P<pk>\d+)/$', views.RenrenClientDetailView.as_view(), name='client-detail'),
		url(r'^oauth/$', views.RenrenClientOauthView.as_view(), name='oauth2'),
		url(r'^callback/$', views.RenrenClientCallbackView.as_view(), name='callback'),
		url(r'^client_delete/(?P<client_id>\d+)/$', views.delete_renrenclient, name='client-delete'),
)


