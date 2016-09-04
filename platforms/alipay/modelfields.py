# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


import decimal

from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator


"""
支付宝用户帐户信息Fields
"""

class AlipayUserTokenField(models.CharField):

	description = "支付宝用户token, String(40)"

	def __init__(self, **kwargs):
		kwargs.setdefault('max_length', 40)
		super(AlipayUserTokenField, self).__init__(**kwargs)

	def get_internal_type(self):
		return "CharField"	


def _isValidAlipayUserId(value):
    value = str(value)
    if not value.startwith('2088'):
    	raise ValidationError, ugettext(u'支付宝用户帐号没有以2088开头')
    if len(value) != 16:
    	raise ValidationError, ugettext(u'支付宝用户帐号没有到16位')

class AlipayUserIdField(models.CharField):
	default_validators = [_isValidAlipayUserId]

	description = "支付宝用户Id Field, String(16), 以 2088 开头的纯 16 位数 字。"

	def __init__(self, **kwargs):
		kwargs.setdefault('max_length', 16)
		super(AlipayUserIdField, self).__init__(**kwargs)

	def get_internal_type(self):
		return "CharField"



try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayUserIdField"])
except ImportError:
    pass






