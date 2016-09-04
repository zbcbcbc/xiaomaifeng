# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.db.models import signals
from django.utils.translation import ugettext_noop as _

from notification import models as notification

def create_notice_types(app, created_models, verbosity, **kwargs):
    notification.create_notice_type("alipay_goodsent_success", _(u"物品寄送认证成功"), _(u"物品寄送认证成功， 通知买家物品已寄送"))
    notification.create_notice_type("alipay_goodsent_fail", _(u"物品寄送认证失败"), _(u"物品寄送认证失败， 通知卖家重新认证"))

signals.post_syncdb.connect(create_notice_types, sender=notification)
