# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
		url(r'^itemlist/$', views.ItemListView.as_view(), name='itemlist'),
		url(r'^fundlist/$', views.FundListView.as_view(), name='fundlist'),
		url(r'^eventlist/$', views.EventListView.as_view(), name='eventlist'),

		url(r'^additem/physical/$', views.CreatePhysicalItemView.as_view(), name='additem-physical'),
		url(r'^additem/digital/$', views.CreateDigitalItemView.as_view(), name='additem-digital'),
		url(r'^additem/event/$', views.CreateEventItemView.as_view(), name='additem-event'),
		url(r'^addfund/donation/$', views.CreateDonationFundView.as_view(), name='addfund-donation'),
		url(r'^addfund/payback/$', views.CreatePaybackFundView.as_view(), name='addfund-payback'),

		url(r'^item_update/physical/(?P<pk>\d+)/$', views.UpdatePhysicalItemView.as_view(), name='item-update-physical'),
		url(r'^item_update/digital/(?P<pk>\d+)/$', views.UpdateDigitalItemView.as_view(), name='item-update-digital'),
		url(r'^item_update/event/(?P<pk>\d+)/$', views.UpdateEventItemView.as_view(), name='item-update-event'),
		url(r'^fund_update/donation/(?P<pk>\d+)/$', views.UpdateDonationFundView.as_view(), name='fund-update-donation'),
		url(r'^fund_update/payback/(?P<pk>\d+)/$', views.UpdatePaybackFundView.as_view(), name='fund-update-payback'),

		url(r'^item_detail/physical/(?P<pk>\d+)/$', views.PhysicalItemView.as_view(), name='item-detail-physical'),
		url(r'^item_detail/digital/(?P<pk>\d+)/$', views.DigitalItemView.as_view(), name='item-detail-digital'),
		url(r'^item_detail/event/(?P<pk>\d+)/$', views.EventItemView.as_view(), name='item-detail-event'),
		url(r'^fund_detail/donation/(?P<pk>\d+)/$', views.DonationFundView.as_view(), name='fund-detail-donation'),
		url(r'^fund_detail/payback/(?P<pk>\d+)/$', views.PaybackFundView.as_view(), name='fund-detail-payback'),
		
		url(r'^delete_fund/donation/(?P<pk>\d+)/$', views.DeleteDonationFundView.as_view(), name='delete-fund-donation'),
		url(r'^delete_fund/payback/(?P<pk>\d+)/$', views.DeletePaybackFundView.as_view(), name='delete-fund-payback'),
		url(r'^delete_item/digital/(?P<pk>\d+)/$', views.DeleteDigitalItemView.as_view(), name='delete-item-digital'),
		url(r'^delete_item/physical/(?P<pk>\d+)/$', views.DeletePhysicalItemView.as_view(), name='delete-item-physical'),
		url(r'^delete_item/event/(?P<pk>\d+)/$', views.DeleteEventItemView.as_view(), name='delete-item-event'),

		url(r'^eventitem/(?P<pk>\d+)/attenders/$', views.EventItemAttendersView.as_view(), name='event-attenders'),
)
