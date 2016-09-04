# -*- coding: utf-8 -*-

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _


from notification import models as notification

def create_notice_types(app, created_models, verbosity, **kwargs):
	notification.create_notice_type("renren_create_post_success", _(u"发布人人状态或照片成功"), _(u"提醒用户在人人上发布了状态或者照片"))

signals.post_syncdb.connect(create_notice_types, sender=notification)