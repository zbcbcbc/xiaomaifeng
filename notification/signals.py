# -*- coding: utf-8 -*-
__author__ = "pinax"
__repo__ = "https://github.com/pinax/django-notification"
__editor__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import django.dispatch


# pylint: disable-msg=C0103
emitted_notices = django.dispatch.Signal(
    providing_args=["batches", "sent", "sent_actual", "run_time"]
)
