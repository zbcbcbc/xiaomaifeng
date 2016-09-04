# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "ubernostrum "
__repo__ = "https://bitbucket.org/ubernostrum/django-registration/"
__editor__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


"""
Backwards-compatible URLconf for existing django-registration
installs; this allows the standard ``include('registration.urls')`` to
continue working, but that usage is deprecated and will be removed for
django-registration 1.0. For new installs, use
``include('registration.backends.default.urls')``.

"""

import warnings

warnings.warn("include('accounts.urls') is deprecated; use include('registration.backends.default.urls') instead.",
              DeprecationWarning)

from accounts.backends.default.urls import *
