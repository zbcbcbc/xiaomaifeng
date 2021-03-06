# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "ubernostrum "
__repo__ = "https://bitbucket.org/ubernostrum/django-accounts//"
__editor__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


"""
URL patterns for the views included in ``django.contrib.auth``.

Including these URLs (via the ``include()`` directive) will set up the
following patterns based at whatever URL prefix they are included
under:

* User login at ``login/``.

* User logout at ``logout/``.

* The two-step password change at ``password/change/`` and
  ``password/change/done/``.

* The four-step password reset at ``password/reset/``,
  ``password/reset/confirm/``, ``password/reset/complete/`` and
  ``password/reset/done/``.

The default accounts/ backend already has an ``include()`` for
these URLs, so under the default setup it is not necessary to manually
include these views. Other backends may or may not include them;
consult a specific backend's documentation for details.

"""
from django.core.urlresolvers import reverse_lazy
from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url

from django.contrib.auth import views as auth_views


urlpatterns = patterns('',
					   url(r'^login/$',
						   auth_views.login,
						   {'template_name': 'accounts/login.html'},
						   name='auth_login'),
					   url(r'^logout/$',
						   auth_views.logout,
						   {'template_name': 'accounts/logout.html'},
						   name='auth_logout'),
					   url(r'^password/change/$',
					   		auth_views.password_change,
					   		{'template_name': 'accounts/password_change_form.html',
					   		'post_change_redirect': reverse_lazy('dashboard:profile:index')},
						   name='auth_password_change'),
					   url(r'^password/change/done/$',
					   		auth_views.password_change_done,
					   		{'template_name': 'accounts/password_change_done.html'},
						   name='auth_password_change_done'),
					   url(r'^password/reset/$',
						   auth_views.password_reset,
						   {'template_name': 'accounts/password_reset_form.html', 
						   'post_reset_redirect': reverse_lazy('accounts:auth_password_reset_done'),
						   'email_template_name': 'accounts/password_reset_email.html'
						   },
						   name='auth_password_reset'),
					   url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
						   auth_views.password_reset_confirm,
						   {'template_name': 'accounts/password_reset_confirm.html', 
						   'post_reset_redirect': reverse_lazy('accounts:auth_password_reset_complete')},
						   name='auth_password_reset_confirm'),
					   url(r'^password/reset/complete/$',
						   auth_views.password_reset_complete,
						   {'template_name': 'accounts/password_reset_complete.html'},
						   name='auth_password_reset_complete'),
					   url(r'^password/reset/done/$',
						   auth_views.password_reset_done,
						   {'template_name': 'accounts/password_reset_done.html'},
						   name='auth_password_reset_done'),
)
