#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging

import redis

from notification import models as notification


logger = logging.getLogger('xiaomaifeng.platforms')



def create_weibopost_success(sender, **kwargs):
    """
    微博用户发布微博成功, 提醒用户
    传入参数 kwargs:{"user", "client", "post", "content"}
    """
    try:
        user = kwargs['user']
        client = kwargs['client']
        post = kwargs['post']
        merchandise = kwargs['merchandise']

        logger.info(u"发送%s发布成功醒邮件给%s..." % (post, user))

        notification.send([user], "sinaweibo_create_post_success", {"client":client,
                            "post":post,
                            "merchandise":merchandise})
    except Exception, err:
        logger.error(u"发送%s发布成功醒邮件给%s 失败，原因: %s" % (post, payer, err))
        pass



