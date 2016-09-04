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
    notification.create_notice_type("membership_expired", _(u"用户会员过期"), _(u"用户会员过期，随时到网站可以更新"))
    notification.create_notice_type("membership_auto_renew", _(u"用户自动更新"), _(u"用户会员已经自动更新"))

signals.post_syncdb.connect(create_notice_types, sender=notification)