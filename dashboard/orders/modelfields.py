# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext
from django.core.exceptions import ValidationError

"""
Order status choices Model Field
"""

__all__ = ["OrderStatus", "OrderStatusField",]


logger = logging.getLogger('xiaomaifeng.orders')


class OrderStatus:
    CREATED = 'created'
    PAYMENT_VERIFIED = 'payment_verified'
    SHIPPMENT_CONFIRMMED = 'shippment_confirmmed'
    SHIPPMENT_RECEIVED = 'shippment_received'
    SUCCEED= 'succeed'
    FAILED = 'failed'

ORDER_STATUS_CHOICES = (
    (OrderStatus.CREATED, u"交易建立"),
    (OrderStatus.PAYMENT_VERIFIED, u"支付确认"),
    (OrderStatus.SHIPPMENT_CONFIRMMED, u"货物寄出"),
    (OrderStatus.SHIPPMENT_RECEIVED, u"货物收到"),
    (OrderStatus.SUCCEED, u"交易成功"),
    (OrderStatus.FAILED, u"交易失败"),
)

#COUNTRIES.append(('ZZ', _('其他')))

def _isValidOrderStatus(value):
    if not value in [lang[0] for lang in ORDER_STATUS_CHOICES]:
        raise ValidationError, ugettext(u"invalid order status")

class OrderStatusField(models.CharField):
    default_validators = [_isValidOrderStatus]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 20)
        kwargs.setdefault('choices', ORDER_STATUS_CHOICES )
        super(OrderStatusField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"



