# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
	url(r'^ticketlist/$', views.TicketPassListView.as_view(), name='ticketlist'),
	url(r'^digitalfilelist/$', views.DigitalFilePassListView.as_view(), name='digitalfilelist'),
	url(r'^digitalfilepass/(?P<pk>\d+)/$', views.DigitalFilePassDetailView.as_view(), name='digitalfilepass-detail'),
	url(r'^digitalfilepass/output/(?P<access_key>\w+)/$', views.DigitalFileOutputView.as_view(), name='digitalfile-output'),
	url(r'^digitalfilepass/download/(?P<access_key>\w+)/$', views.DigitalFileDownloadView.as_view(), name='digitalfile-download'),
	url(r'^ticketpass/(?P<pk>\d+)/$', views.TicketPassDetailView.as_view(), name='ticketpass-detail'),
	url(r'^ticketpass/output/(?P<access_key>\w+)/$', views.TicketOutputView.as_view(), name='ticket-output'),
	url(r'^ticketpass/download/(?P<access_key>\w+)/$', views.TicketDownloadView.as_view(), name='ticket-download'),
	url(r'^ticketpass_verify/(?P<pk>\d+)/$', views.TicketPassVerifyView.as_view(), name='ticket-verify'),
)
