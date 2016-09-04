# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _

from notification import models as notification

def create_notice_types(app, created_models, verbosity, **kwargs):
    notification.create_notice_type("deliver_ticketpass", _(u"发送门票给用户"), _(u"门票创建成功，发送门票给用户"))
    notification.create_notice_type("deliver_digitalfilepass", _(u"发送虚拟物品给用户"), _(u"虚拟物品创建成功，发送虚拟物品给用户"))

signals.post_syncdb.connect(create_notice_types, sender=notification)