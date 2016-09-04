# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    #TODO: hash urls to make them less recognizable
    url(r'^directpay_return_url/$', views.directpay_return_url_handler, name="directpay-return-url"),
    url(r'^directpay_notify_url/$', views.directpay_notify_url_handler, name="directpay-notify_url"),
    url(r'^partnertrade_return_url/$', views.partnertrade_return_url_handler, name="partnertrade-return_url"),
    url(r'^partnertrade_notify_url/$', views.partnertrade_notify_url_handler, name="partnertrade-notify-url"),
)