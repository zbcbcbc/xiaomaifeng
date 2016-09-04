# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



import urllib, datetime, logging
from urllib import urlencode, urlopen

from django.utils import timezone as djtimezone
from django.db import models, connection, IntegrityError
from django.db.models.signals import pre_delete, post_save, post_delete
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic



from platforms.models import *
from alipay_python import *
from modelfields import *



logger = logging.getLogger('xiaomaifeng.platforms')





class AlipayClientManager(ClientBaseManager):

	def get_authorize_url(self, redirect_uri=None, mac=False, **kwargs):
		"""
		返回支付宝授权url,可能有错
		TODO, CACHE it
		"""
		args = dict(client_id=ALIPAY_APP_KEY, callback_url=redirect_uri)
		args["scope"] = 'p'
		args["response_type"] = ALIPAY_RESPONSE_TYPE
		#args["scope"] = 'P'
		return ALIPAY_AUTHORIZATION_URI + "?" + urllib.urlencode(args)  


class AlipayClient(ClientBase):
	"""
	支付宝用户核心数据
	"""

	alipay_user_email = models.EmailField(max_length=100, null=True, editable=False)
	user_status = models.CharField(max_length=10, null=True, editable=False) # 用户状态。可选:normal(正常), supervise (监管),delete(注销)
	user_type = models.CharField(max_length=10, null=True, editable=False) # 用户类型。可选：personal（个人），company（公司）
	certified = models.NullBooleanField(null=True, editable=False) # 是否通过实名认证
	real_name = models.CharField(max_length=100, null=True, editable=False)
	logon_id = models.CharField(max_length=100, null=True, editable=False) # 支付宝登录号

	# 帐户信息
	total_amount = models.PositiveIntegerField(default=0, null=True, blank=True, editable=False) # 余额总额
	available_amount = models.PositiveIntegerField(default=0, null=True, blank=True, editable=False) # 可用余额
	freeze_amount = models.PositiveIntegerField(default=0, null=True, blank=True, editable=False) # 不可用余额


	class Meta(ClientBase.Meta):
		permissions = (
			('can_post',u'可以发布'),
		)

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)


	def get_absolute_url(self):
		return reverse('platforms:alipay:client-detail', args=[str(self.id)])


	def save(self, *args, **kwargs):
		super(ClientBase, self).save(*args, **kwargs)


	def _get_client_info(self, write_to_db=True, **kwargs):
		"""
		STUB
		"""
		return


	def update_client_profile(self, write_to_db=True, **kwargs):
		"""
		STUB
		"""
		return








