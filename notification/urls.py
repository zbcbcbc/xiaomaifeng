# -*- coding: utf-8 -*-
__author__ = "pinax"
__repo__ = "https://github.com/pinax/django-notification"
__editor__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.conf.urls import patterns, url

from notification.views import notice_settings


urlpatterns = patterns('',
    url(r'^settings/$', notice_settings, name="notification_notice_settings"),
)
