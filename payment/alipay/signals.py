# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from django.dispatch import Signal


# 支付宝寄货确认信号
alipay_goodsent_success_signal = Signal(providing_args=["instance"])
alipay_goodsent_fail_signal = Signal(providing_args=["instance", "reason", "re_revify"])

