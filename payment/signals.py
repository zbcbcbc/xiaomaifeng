# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from django.dispatch import Signal



payment_verify_success_signal = Signal(providing_args=["payment"])
payment_verify_fail_signal = Signal(providing_args=["instance", "reason", "re_verify"])

shippment_confirm_success_signal = Signal(providing_args=["payment"])