# -*- coding: utf-8 -*-

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from django.dispatch import Signal



create_renrenpost_success_signal = Signal(providing_args=["user", "client", "post", "merchandise"])
