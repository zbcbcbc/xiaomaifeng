# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import datetime
import pytz

from django.test import TestCase
from django.contrib.auth.models import User

from models import TicketPass

class TicketPassTestCase(TestCase):

	def test_ticket_can_generate(self):
		owner = User.objects.create_user('zbcbcbc3', 'zbcbcbc3@gmail.com', 'zbcbcbc3')
		distributor = User.objects.create_user('zbcbcbc4', 'zbcbcbc4@gmail.com', 'zbcbcbc4')
		title = u'我要举办一场个人签名秀'
		url = 'http://www.xiaomaifeng.com/dashboard/passbook/verify/'
		qr_image_height = 100
		qr_image_width = 100

		event_start = datetime.datetime.now()
		event_end = datetime.datetime.now() + datetime.timedelta(hours=24)

		time_zone = 'Asia/Shanghai'

		ticket = TicketPass(owner=owner, distributor=distributor, title=title, url=url, 
							qr_image_height=qr_image_height,
							qr_image_width=qr_image_width,
							event_start=event_start,
							event_end=event_end,
							time_zone=time_zone)
		ticket.save()


