# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.conf.urls import patterns, url

from dashboard.orders import views

urlpatterns = patterns('', 
		url(r'^buy/$', views.BuyOrderListView.as_view(), name='buylist'),
		url(r'^sell/$', views.SellOrderListView.as_view(), name='selllist'),
		url(r'^order/(?P<pk>\d+)/$', views.OrderDetailView.as_view(), name='order-detail'),
		url(r'^verify/(?P<pk>\d+)/$', views.VerifyOrderView.as_view(), name='verify'),
		url(r'^cancel/buyer/(?P<pk>\d+)/$', views.BuyerCancelOrderView.as_view(), name='cancel-buyer'),
		url(r'^cancel/seller/(?P<pk>\d+)/$', views.SellerCancelOrderView.as_view(), name='cancel-seller'),
)
