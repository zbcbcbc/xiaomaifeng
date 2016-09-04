# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.conf.urls import patterns, include, url


urlpatterns = patterns('', 
		url(r'^renren/', include('platforms.renren.urls', namespace='renren')),
		url(r'^weibo/', include('platforms.weibo.urls', namespace='weibo')),
		url(r'^alipay/', include('platforms.alipay.urls', namespace='alipay')),
        url(r'^douban/', include('platforms.douban.urls', namespace='douban')),
)
