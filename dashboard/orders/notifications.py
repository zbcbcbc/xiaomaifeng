# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.db.models import signals
from django.utils.translation import ugettext_noop as _

from notification import models as notification   

def create_notice_types(app, created_models, verbosity, **kwargs):
	notification.create_notice_type("order_verify_physicalitem", _(u"实体物品交易认证"), _(u"实体物品交易认证"))
	notification.create_notice_type("order_verify_digitalitem", _(u"虚拟物品交易认证"), _(u"虚拟物品交易认证"))
	notification.create_notice_type("order_verify_eventitem", _(u"活动门票交易认证"), _(u"活动门票交易认证"))
	notification.create_notice_type("order_verify_paybackfund", _(u"普通筹资交易认证"), _(u"普通筹资交易认证"))
	notification.create_notice_type("order_verify_donationfund", _(u"捐款交易认证"), _(u"捐款交易认证"))
	
	notification.create_notice_type("order_verify_success_physicalitem", _(u"实体物品交易认证成功"), _(u"实体物品交易认证成功"))
	notification.create_notice_type("order_verify_success_digitalitem", _(u"虚拟物品交易认证成功"), _(u"虚拟物品交易认证成功"))
	notification.create_notice_type("order_verify_success_eventitem", _(u"活动门票交易认证成功"), _(u"活动门票交易认证成功"))
	notification.create_notice_type("order_verify_success_paybackfund", _(u"普通筹资交易认证成功"), _(u"普通筹资交易认证成功"))
	notification.create_notice_type("order_verify_success_donationfund", _(u"捐款交易认证成功"), _(u"捐款交易认证成功"))

	notification.create_notice_type("create_order_fail", _(u"交易创建失败"), _(u"交易创建失败，通知买家失败原因"))
	notification.create_notice_type("order_payment_verify_success", _(u"交易支付认证成功"), _(u"交易支付认证成功，通知买家认证成功，通知卖家寄货"))   
	notification.create_notice_type("order_payment_verify_fail", _(u"交易支付认证失败"), _(u"交易支付认证失败，通知买家失败原因"))
	
signals.post_syncdb.connect(create_notice_types, sender=notification)