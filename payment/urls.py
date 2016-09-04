#!/usr/bin/python
#-*- coding:utf-8 -*-
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from django.conf.urls import patterns, include, url
#from django.views.generic.simple import direct_to_template
import views

urlpatterns = patterns('',
	url(r'^alipay/', include('payment.alipay.urls', namespace='alipay')),
)
