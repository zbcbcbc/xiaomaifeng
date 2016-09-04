# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import datetime, logging, pytz

from django.contrib.auth.models import User
from django.utils import timezone as djtimezone
from django.core import mail
from django.test import TestCase
from django.db import IntegrityError, DataError

from dashboard.passbook.models import TicketPass
from dashboard.listing.models import EventItem


logging.disable(logging.CRITICAL)


class TicketPassTestCase(TestCase):

	def setUp(self):
		# initiate one correct ticket
		try:
			ticket = TicketPass.objects.get(title__exact=u"测试门票")
			ticket.delete()
		except:
			pass

		self.ticket_distributor = User.objects.create_user(username='ticketseller', password='ticketseller', email='zhang368@illinois.edu')
		self.ticket_owner = User.objects.create_user(username='ticketowner', password='ticketowner', email='zhang368@illinois.edu')
		self.ticket_distributor.is_active = True
		self.ticket_distributor.save()
		self.ticket_owner.is_active = True
		self.ticket_owner.save()
		self.assertEqual(self.ticket_distributor .is_active, True)
		self.assertEqual(self.ticket_owner.is_active, True)

		time_zone = pytz.timezone('Asia/Shanghai')
		expire_date = djtimezone.now().astimezone(time_zone) + datetime.timedelta(hours=12)
		event_start = expire_date + datetime.timedelta(hours=12)


		self.test_ticket_event = EventItem.objects.create(user=self.ticket_distributor,
											name=u"测试门票活动",
											price=10,
											availability=10,
											description=u"用来测试门票的活动",
											expire_date=expire_date,
											event_start=event_start)





	def test_ticketpass_create(self):
		"""
		测试ticketpass 是否pass model fields 限制
		"""

		title = u'测试门票'
		url = 'www.xiaomaifeng.com/passbook/'
		event_start = datetime.datetime.now() # should be timezone aware
		time_zone = pytz.timezone('Asia/Shanghai')

		ticket = TicketPass.objects.create(owner=self.ticket_owner, 
										distributor=self.ticket_distributor, 
										title=title,
										url=url,
										event=self.test_ticket_event,
										event_start=event_start,
										time_zone=time_zone)

		ticket = TicketPass.objects.get(pk=ticket.pk)

		self.assertEqual(ticket.owner_id, self.ticket_owner.pk)
		self.assertEqual(ticket.distributor_id, self.ticket_distributor.pk)
		self.assertEqual(ticket.title, title)
		self.assertEqual(ticket.url, url)
		self.assertEqual(ticket.event_id, self.test_ticket_event.id)
		#self.assertEqual(ticket.qr_image_height, qr_image_height)
		#self.assertEqual(ticket.qr_image_width, qr_image_width)
		#self.assertEqual(ticket.event_start, event_start)
		self.assertEqual(ticket.is_used, False)



		ticket_create = TicketPass.objects.create

		title = u'错误门票'
		url = 'www.xiaomaifeng.com/passbook/'
		event_start = datetime.datetime.now() # should be timezone aware

		# missing owner
		self.assertRaisesMessage(IntegrityError, "Column 'owner_id' cannot be null", callable_obj=ticket_create, 
							distributor=self.ticket_distributor,
							title=title,
							event=self.test_ticket_event,
							url=url,
							event_start=event_start,
							time_zone=time_zone)

		# missing distributor
		self.assertRaisesMessage(IntegrityError, "Column 'distributor_id' cannot be null", callable_obj=ticket_create, 
							owner=self.ticket_owner,
							title=title,
							event=self.test_ticket_event,
							url=url,
							event_start=event_start,
							time_zone=time_zone)	

		# bad title
		# ---- title too long (larger than 128 length in Chinese)
		bad_title = u"这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串\
					这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串\
					这是个十个字的字符串这是个十个字的字符串这是个十个字的字符" # 129
		self.assertRaisesMessage(DataError, "Data too long for column 'title'", callable_obj=ticket_create, 
							owner=self.ticket_owner,
							distributor=self.ticket_distributor,
							title=bad_title,
							url=url,
							event_start=event_start,
							time_zone=time_zone)



		# TODO: event_start time timezone conversion


	def test_ticketpass_create_ticketpass(self):
		title = u'正确门票'
		url = 'www.xiaomaifeng.com/passbook/'
		event_start = datetime.datetime.now() # should be timezone aware
		time_zone = pytz.timezone('Asia/Shanghai')

		# correct ticket creation
		ticket = TicketPass.objects.create_ticketpass(owner_id=self.ticket_owner.id, 
												distributor_id=self.ticket_distributor.id,
												event_id=self.test_ticket_event.id, 
												title=title,
												event_start=event_start, 
												time_zone=time_zone,
												deliver=False)

		ticket = TicketPass.objects.get(pk=ticket.pk)

		self.assertEqual(ticket.distributor_id, self.ticket_distributor.id)
		self.assertEqual(ticket.owner_id, self.ticket_owner.id)
		self.assertEqual(ticket.title, title)
		self.assertEqual(ticket.url, url)
		ticket.delete()

		# error creation, same distributor and owner
		title = u"错误门票"
		ticket = TicketPass.objects.create_ticketpass(owner_id=self.ticket_owner.id, 
												distributor_id=self.ticket_owner.id, 
												event_id=self.test_ticket_event.id, 
												title=title, 
												event_start=event_start, 
												time_zone=time_zone,
												deliver=False)	
		self.assertEqual(ticket, None)






	def test_ticketpass_deliver_to_owner(self):
		title = u'正确门票'
		url = 'www.xiaomaifeng.com/passbook/'
		event_start = datetime.datetime.now() # should be timezone aware
		time_zone = pytz.timezone('Asia/Shanghai')

		# correct ticket creation and delivery
		ticket = TicketPass.objects.create_ticketpass(owner_id=self.ticket_owner.id, 
												distributor_id=self.ticket_distributor.id,
												event_id=self.test_ticket_event.id, 
												title=title,
												event_start=event_start, 
												time_zone=time_zone,
												deliver=True)

		ticket = TicketPass.objects.get(pk=ticket.pk)

		self.assertEqual(len(mail.outbox), 1)
		self.assertEqual(mail.outbox[0].to, [ticket.owner.email])
		mail.outbox = []
		# deliver to user directly
		ticket.deliver_to_owner()
		self.assertEqual(len(mail.outbox), 1)
		self.assertEqual(mail.outbox[0].to, [ticket.owner.email])




		

	def test_verify_ticket(self):
		title = u'正确门票'
		url = 'www.xiaomaifeng.com/passbook/'
		event_start = datetime.datetime.now() # should be timezone aware
		time_zone = pytz.timezone('Asia/Shanghai')

		# correct ticket creation
		ticket = TicketPass.objects.create_ticketpass(owner_id=self.ticket_owner.id, 
												distributor_id=self.ticket_distributor.id,
												event_id=self.test_ticket_event.id, 
												title=title,
												event_start=event_start, 
												time_zone=time_zone,
												deliver=False)

		# first time verify
		status, msg = TicketPass.objects.verify_ticket(ticket_id=ticket.pk,
												distributor_id=ticket.distributor_id)		
		self.assertEqual(status, True)


		# one ticket can only be verified to true once
		status, msg = TicketPass.objects.verify_ticket(ticket_id=ticket.pk,
												distributor_id=ticket.distributor_id)		
		self.assertEqual(status, False)

		ticket.is_used = True
		ticket.save()

		# not distributor himself
		status, msg = TicketPass.objects.verify_ticket(ticket_id=ticket.pk,
												distributor_id=int(ticket.distributor_id)+1)
		self.assertEqual(status, False)














		