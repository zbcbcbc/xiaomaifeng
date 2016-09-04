#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging

from notification import models as notification

logger = logging.getLogger('site.signals.douban')



def create_doubanpost_success(sender, **kwargs):
    """
    豆瓣用户发布Mini广播成功, 提醒用户
    传入参数 kwargs:{"user", "client", "post", "content"}
    """
    try:
        user = kwargs['user']
        client = kwargs['client']
        post = kwargs['post']
        merchandise = kwargs['merchandise']

        logger.info(u"发送%s发布成功醒邮件给%s..." % (post, user))

        notification.send([user], "douban_create_post_success", {"client":client,
                            "post":post,
                            "merchandise":merchandise})
    except Exception, err:
        logger.error(u"发送%s发布成功醒邮件给%s 失败，原因: %s" % (post, payer, err))
        pass


