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
在这里定义支付宝的数据Field,让网站的物品Item,筹资Fund, 用户资料直接享用这些Field避免数据冲突
"""


"""
支付宝基本参数Fields
"""

class AlipayTradeNoField(models.CharField):
	
	description = "支付宝交易ID, String(64)"

	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 64)
		super(AlipayTradeNoField, self).__init__(*args, **kwargs)

	def get_internal_type(self):
		return "CharField"

"""
支付宝商品信息Fields
"""

class AlipaySubjectField(models.CharField):

	description = "String(256) 商品的标题/交易标题/订单 标题/订单关键字等。"

	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 128) # DatabaseError: (1071, 'Specified key was too long; max key length is 767 bytes')
		super(AlipaySubjectField, self).__init__(*args, **kwargs) 

	def get_internal_type(self):
		return "CharField"


class AlipayDateTimeField(models.DateTimeField):

	description = "支付宝时间Field yyyy-MM-dd HH:mm:ss。"

	def __init__(self, **kwargs):
		super(AlipayDateTimeField, self).__init__(**kwargs)

	def get_internal_type(self):
		return "DateTimeField"


class AlipayPriceField(models.DecimalField):
	description = "支付宝物品价格Field, 单位为:RMB Yuan。取值 范围为 [0.01,1000000.00],精确 到小数点后两位。 "
	
	default_validators = [MaxValueValidator(1000000.00), MinValueValidator(0.01)]

	def __init__(self, verbose_name=None, currency=None, **kwargs):
		self.currency = currency #TODO: set YUAN
		kwargs.setdefault('decimal_places', 2)
		kwargs.setdefault('max_digits', 9)
		#kwargs.setdefault()
		super(AlipayPriceField, self).__init__(verbose_name, **kwargs)

	def get_internal_type(self):
		return "DecimalField"


class AlipayTotalFeeField(models.DecimalField):
	description = "支付宝总共费用Field, 该笔订单的资金总额,单位为 RMB-Yuan。取值范围为[0.01, 100000000.00],精确到小数点后 两位"

	default_validators = [MaxValueValidator(100000000.00), MinValueValidator(0.01)]

	def __init__(self, **kwargs):
		kwargs.setdefault('decimal_places', 2)
		kwargs.setdefault('max_digits', 11)
		super(AlipayTotalFeeField, self).__init__(**kwargs)

	def get_internal_type(self):
		return "DecimalField"



"""
以下是支付宝收货人信息Fields
"""

class AlipayReceiverNameField(models.CharField):

	description = "支付宝收货用户姓名Field, String(128)"

	def __init__(self, **kwargs):
		kwargs.setdefault('max_length', 128)
		super(AlipayReceiverNameField, self).__init__(**kwargs)		

	def get_internal_type(self):
		return "CharField"


class AlipayReceiverAddressField(models.CharField):

	description = "支付宝收货用户地址Field, String(256)"

	def __init__(self, **kwargs):
		kwargs.setdefault('max_length', 256)
		super(AlipayReceiverAddressField, self).__init__(**kwargs)

	def get_internal_type(self):
		return "CharField"


class AlipayReceiverZipField(models.CharField):

	description = "支付宝收货用户Zip code field, String(20)"

	def __init__(self, **kwargs):
		kwargs.setdefault('max_length', 20)
		super(AlipayReceiverZipField, self).__init__(**kwargs)

	def get_internal_type(self):
		return "CharField"




class AlipayReceiverMobileField(models.CharField):

	description = "支付宝收货用户手机Field, String(30)"

	def __init__(self, **kwargs):
		kwargs.setdefault('max_length', 20)
		super(AlipayReceiverMobileField, self).__init__(**kwargs)

	def get_internal_type(self):
		return "CharField"


"""
以下是支付宝物流Fields
"""

class AlipayLogisticsNameField(models.CharField):

	description = "支付宝担保交易物名称Field, String(64)"

	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 64)
		super(AlipayLogisticsNameField, self).__init__(*args, **kwargs)

	def get_internal_type(self):
		return "CharField"




LOGISTICS_TYPES = [
	('POST', u'平邮'),
	('EXPRESS', u'高速快递'),
	('EMS', u'EMS'),
	('DIRECT', u'无需物流')
]

def _isValidLogisticsType(value):
	if not value in [lang[0] for lang in LOGISTICS_TYPES]:
		raise ValidationError, ugettext(u"无效的物流类型选择")


class AlipayLogisticsTypeField(models.CharField):
	description = "支付宝担保交易物流类型Field, String(30)"

	default_validators = [_isValidLogisticsType]

	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 10)
		kwargs.setdefault('choices', LOGISTICS_TYPES)
		super(AlipayLogisticsTypeField, self).__init__(*args, **kwargs)

	def get_internal_type(self):
		return "CharField"



LOGISTICS_PAYMENT_TYPES = [
	('BUYER_PAY', u'物流买家承担运费'),
	('SELLER_PAY', u'物流卖家承担运费'),
	('BUYER_PAY_AFTER_RECEIVE', u'买家到货付款,运费显示但不计入总价')
]

def _isValidLogisticsPaymentType(value):
	if not value in [lang[0] for lang in LOGISTICS_PAYMENT_TYPES]:
		raise ValidationError, ugettext(u"无效的物流支付类型选择")


class AlipayLogisticsPaymentField(models.CharField):
	description = "支付宝担保交易物流支付类型Field, String(30)"

	default_validators = [_isValidLogisticsPaymentType]

	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 20)
		kwargs.setdefault('choices', LOGISTICS_PAYMENT_TYPES)
		super(AlipayLogisticsPaymentField, self).__init__(*args, **kwargs)

	def get_internal_type(self):
		return "CharField"



class AlipayLogisticsFeeField(models.DecimalField):
	description = "支付宝担保交易物流费用Field, 单位为:RMB Yuan。精确 到小数点后两位。缺省值为 0 元。"

	default_validators = [MaxValueValidator(1000000.00), MinValueValidator(0.00)]

	def __init__(self, verbose_name=None, currency=None, **kwargs):
		self.currency = currency #TODO: set YUAN
		kwargs.setdefault('decimal_places', 2)
		kwargs.setdefault('max_digits', 9)
		#kwargs.setdefault()
		super(AlipayLogisticsFeeField, self).__init__(verbose_name, **kwargs)

	def get_internal_type(self):
		return "DecimalField"





try:
	from south.modelsinspector import add_introspection_rules
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayTradeNoField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipaySubjectField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayDateTimeField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayPriceField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayTotalFeeField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayReceiverNameField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayReceiverAddressField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayReceiverZipField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayReceiverMobileField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayLogisticsNameField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayLogisticsTypeField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayLogisticsPaymentField"])
	add_introspection_rules([], ["^platform\.alipay\.modelfields\.AlipayLogisticsFeeField"])
except ImportError:
	pass






