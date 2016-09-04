# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging

from celery import task as celery_task

from models import Order



logger = logging.getLogger('xiaomaifeng.orders')



@celery_task(ignore_result=True)
def create_order_task(buyer, seller, comment, social_platform, body, merchandise, quantity):

	logger.warning('creating order...')

	Order.objects.create_order(buyer=buyer, seller=seller, comment=comment, social_platform=social_platform, 
				body=body, merchandise=merchandise, quantity=quantity)




