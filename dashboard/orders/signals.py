# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from django.dispatch import Signal


# 创建交易信号
create_order_success_signal = Signal(providing_args=["order", "payment"])
create_order_fail_signal = Signal(providing_args=["payer","body","comment","social_platform","quantity","reason"])
