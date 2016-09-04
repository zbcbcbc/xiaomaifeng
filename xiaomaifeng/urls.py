# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'jifu.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
	url(r'^', include('home.urls', namespace='home')), 
	url(r'^accounts/', include('accounts.backends.default.urls', namespace='accounts')),
	url(r'^dashboard/', include('dashboard.urls', namespace='dashboard')),
	url(r'^platforms/', include('platforms.urls', namespace='platforms')), 
	url(r'^payment/', include('payment.urls', namespace='payment')),
)


if settings.DEBUG:
	# static files (images, css, javascript, etc.)
	urlpatterns += patterns('',
    	(r'^(?P<path>.*)$', 'django.views.static.serve', {
    	'document_root': settings.MEDIA_ROOT})
    )

if "notification" in settings.INSTALLED_APPS:
	urlpatterns += patterns('', 
		url(r'^notification/', include('notification.urls', namespace='notification')),
	)




