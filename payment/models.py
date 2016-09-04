# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from django.db import models


__all__ = ['PartnerTradeBaseModel','DirectPayBaseModel', 'PartnerTradeBaseManager', 'DirectPayBaseManager']



class PaymentBaseManager(models.Manager):
	
	def verify_payment(self, params):
		raise NotImplementedError

	def update_payment(self, params):
		raise NotImplementedError


class PaymentBaseModel(models.Model):
	"""
	"""
	xmf_order = models.OneToOneField('orders.Order', primary_key=True, null=False, on_delete=models.CASCADE, 
									blank=False, 
									related_name="%(class)s", 
									editable=False, )

	is_verified = models.BooleanField(null=False, default=False, editable=True)

	class Meta:
		abstract = True

	def __repr__(self):
		return u"%s:(%s)" % (self, self.pk)


	def _verify_success(self, **kwargs):
		"""
		交易认证成功逻辑:
			如果认证成功，发送认证成功信号
		"""
		raise NotImplementedError


	def _verify_fail(self, reason, re_verify=True, **kwargs):
		"""
		交易认证成功逻辑:
			如果认证成功，发送认证失败信号
		"""		
		raise NotImplementedError


	def build_verify_url(self, write_to_db=False, **kwargs):
		"""
		建立支付认证url
		"""
		raise NotImplementedError



class PartnerTradeBaseManager(PaymentBaseManager):

	def create_payment(self, payer, receiver, comment, social_platform, body, item, quantity):

		raise NotImplementedError


class PartnerTradeBaseModel(PaymentBaseModel):


	class Meta(PaymentBaseModel.Meta):
		abstract = True


	def shippment_confirm_success(self, **kwargs):
		"""
		交易货物寄送成功：
			如果认证成功，发送寄送货物成功信号
		"""
		raise NotImplementedError	


	def shippment_confirm_fail(self, reason, re_verify=True, **kwargs):
		"""
		交易货物寄送成功：
			如果认证成功，发送寄送货物成功信号
		"""
		raise NotImplementedError



class DirectPayBaseManager(PaymentBaseManager):

	def create_payment(self, payer, receiver, comment, social_platform, body, fund):

		raise NotImplementedError


class DirectPayBaseModel(PaymentBaseModel):



	class Meta(PaymentBaseModel.Meta):
		abstract = True










  
