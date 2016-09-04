# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging, datetime, pytz

from django.utils import timezone as djtimezone
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError

try:
	from django.db import DataError
except:
	DataError = None

from django.core.exceptions import ValidationError

from dashboard.listing.models import PhysicalItem, DigitalItem, PaybackFund, DonationFund, EventItem
from dashboard.passbook.models import TicketPass

# Create your tests here.

logging.disable(logging.WARNING)




class PhysicalItemTestCase(TestCase):

	def setUp(self):
		user = User.objects.get(username__exact='lalalalavic')
		PhysicalItem.objects.create(user=user,
								name=u"测试物品",
								description=u"正确",
								price=99,
								availability=99,
								purchase_limit=1,
								logistics_fee=10)

	def test_physical_item_create(self):
		user = User.objects.get(username__exact='lalalalavic')

		# test successful creation and attributes retrive
		item = PhysicalItem.objects.create(user=user,
							name=u"正确物品1",
							description=u"正确",
							price=99,
							availability=99,
							purchase_limit=1,
							logistics_fee=10)


		self.assertEqual(item.name, u"正确物品1")
		self.assertEqual(item.description, u"正确")
		self.assertEqual(item.availability, 99)
		self.assertEqual(item.price, 99)
		self.assertEqual(item.purchase_limit, 1)
		self.assertEqual(item.logistics_fee, 10)




		# Test unsuccessful creation and raise integrity error
		# -- test essential attributes

		item_create = PhysicalItem.objects.create
		# ---- user
		# -------- missing
		self.assertRaisesMessage(IntegrityError, "cannot be null", callable_obj=item_create, 
							name=u"错误物品1",
							description=u"正确",
							price=99,
							availability=99,
							purchase_limit=1,
							logistics_fee=10)

		# ---- name
		# -------- duplicate
		self.assertRaisesMessage(IntegrityError, "Duplicate", callable_obj=item_create, 
							user=user,
							name=u"正确物品1",
							description=u"测试物品单一用户重复名称",
							price=99,
							availability=99,
							purchase_limit=1,
							logistics_fee=10)	
	

		# ---- price
		# -------- missing
		self.assertRaisesMessage(IntegrityError, "cannot be null", callable_obj=item_create, 
							user=user,
							name=u"错误物品2",
							description=u"正确",
							#price=99,
							availability=99,
							purchase_limit=1,
							logistics_fee=10)



		# ---- availability
		# -------- missing
		self.assertRaisesMessage(IntegrityError, "'availability' cannot be null", callable_obj=item_create, 
							user=user,
							name=u"错误物品6",
							description=u"正确",
							price=99,
							#availability=99,
							purchase_limit=1,
							logistics_fee=10)

		# -------- out of range	
		if DataError:
			self.assertRaisesMessage(DataError, "Out of range value for column 'availability'", callable_obj=item_create, 
							user=user,
							name=u"错误物品11",
							description=u"正确",
							price=9,
							availability=-99,
							purchase_limit=11,
							logistics_fee=10)	
		

		# ---- purchase limit
		# -------- missing
		item = item_create(user=user,
							name=u"正确物品2",
							description=u"正确",
							price=99,
							availability=999,
							#purchase_limit=1,
							logistics_fee=10)
		self.assertEqual(item.purchase_limit, item.availability)


		# --------- too large
		item = item_create(user=user,
							name=u"正确物品3",
							description=u"正确",
							price=99,
							availability=9,
							purchase_limit=100,
							logistics_fee=10)
		self.assertEqual(item.purchase_limit, 100)	


		# -------- less than 1
		# ------------ -9
		#TODO: it throws dataerror instead
		if DataError:
			self.assertRaisesMessage(DataError, "Out of range value for column 'purchase_limit'", callable_obj=item_create, 
							user=user,
							name=u"错误物品11",
							description=u"正确",
							price=9,
							availability=99,
							purchase_limit=-11,
							logistics_fee=10)		
		

		# ---- logistics_fee
		# -------- default 0
		item = item_create(user=user,
							name=u"正确物品4",
							description=u"测试物品默认物流费用",
							price=99,
							availability=99,
							purchase_limit=1)
		self.assertEqual(item.logistics_fee, 0)



		# ---- logistics_type
		# -------- default POST
		item = item_create(user=user,
							name=u"正确物品5",
							description=u"测试物品默认物流方式",
							price=99,
							availability=99,
							purchase_limit=1)
		self.assertEqual(item.logistics_type, 'POST')

		# ---- logistics_payment
		# -------- default BUYER_PAY
		item = item_create(user=user,
							name=u"正确物品6",
							description=u"测试物品默认物流支付方式",
							price=99,
							availability=99,
							purchase_limit=1)
		self.assertEqual(item.logistics_payment, 'BUYER_PAY')	




	def test_physical_item_availability(self):
		test_item = PhysicalItem.objects.get(name__exact=u"测试物品")
		test_item.availability = 10
		test_item.save()
		self.assertEqual(test_item.availability, 10)

		# in range decrement
		status, test_item = PhysicalItem.objects.decrement_item_availability(test_item, 2)
		self.assertEqual(status, True)
		self.assertEqual(test_item.availability, 8)

		# on limit decrement
		status, test_item = PhysicalItem.objects.decrement_item_availability(test_item, 8)
		self.assertEqual(status, True)
		self.assertEqual(test_item.availability, 0)

		# over limit decrement
		status, test_item = PhysicalItem.objects.decrement_item_availability(test_item, 1)
		self.assertEqual(status, False)
		self.assertEqual(test_item.availability, 0)

		status, test_item = PhysicalItem.objects.increment_item_availability(test_item, 10)
		self.assertEqual(status, True)
		self.assertEqual(test_item.availability, 10)		



	def test_physical_item_image_path(self):
		pass


	def test_physical_item_show_url(self):
		"""
		测试物品的show url 连接可用性
		"""
		pass

	def test_physical_item_get_absolute_url(self):
		"""
		测试物品的get_absolute_url 连接可用性
		"""
		pass


	def test_physical_item_delete(self):
		"""
		测试物品的删除功能
		"""
		pass





class DigitalItemTestCase(TestCase):

	def setUp(self):
		pass


	def test_digital_item_create(self):
		user = User.objects.get(username__exact='lalalalavic')



	def test_generate_qrcontent(self):
		pass


class EventItemTestCase(TestCase):

	def setUp(self):
		user = User.objects.get(username__exact='lalalalavic')
		tz = pytz.timezone('Asia/Shanghai')
		expire_date =  djtimezone.now().astimezone(tz) + datetime.timedelta(hours=12)
		event_start = expire_date + datetime.timedelta(hours=24)

		#print 'expire_date', expire_date
		#print 'expire_date to store in db is aware?:', djtimezone.is_aware(expire_date)

		event_item = EventItem.objects.create(user=user,
								name=u"测试活动",
								description=u"正确的活动用来测试",
								price=99,
								availability=99,
								purchase_limit=1,
								expire_date=expire_date,
								event_start=event_start,
								time_zone=tz)

		event_item = EventItem.objects.get(name__exact=u"测试活动")

		


	def test_event_item_create(self):
		user = User.objects.get(username__exact='lalalalavic')

		# test successful creation and attributes retrive
		# TODO: omit timezone for now
		tz = pytz.timezone('Asia/Shanghai')
		expire_date = datetime.datetime.now().replace(tzinfo=tz)
		event_start = expire_date + datetime.timedelta(hours=12)
		item = EventItem.objects.create(user=user,
							name=u"正确活动",
							description=u"正确",
							price=99,
							availability=99,
							purchase_limit=1,
							expire_date=expire_date,
							event_start=event_start,
							time_zone=tz)

		item = EventItem.objects.get(pk=item.pk)

		self.assertEqual(item.name, u"正确活动")
		self.assertEqual(item.description, u"正确")
		self.assertEqual(item.availability, 99)
		self.assertEqual(item.price, 99)
		self.assertEqual(item.purchase_limit, 1)
		self.assertEqual(item.time_zone, tz)


		# Test unsuccessful creation and raise integrity error
		# -- test essential attributes

		item_create = EventItem.objects.create
		
		# ---- user
		# -------- missing
		self.assertRaisesMessage(IntegrityError, "Column 'user_id' cannot be null", callable_obj=item_create, 
							name=u"错误活动",
							description=u"正确",
							price=99,
							availability=99,
							purchase_limit=1,
							expire_date=expire_date,
							event_start=event_start,
							time_zone=tz)
		# ---- name
		# -------- duplicate
		self.assertRaisesMessage(IntegrityError, "Duplicate", callable_obj=item_create, 
							user=user,
							name=u"正确活动",
							description=u"测试物品单一用户重复名称",
							price=99,
							availability=99,
							purchase_limit=1,
							expire_date=expire_date,
							event_start=event_start,
							time_zone=tz)
	
	
		# ---- price
		# -------- missing
		self.assertRaisesMessage(IntegrityError, "Column 'price' cannot be null", callable_obj=item_create, 
							user=user,
							name=u"错误活动",
							description=u"正确",
							#price=99,
							availability=99,
							purchase_limit=1,
							expire_date=expire_date,
							event_start=event_start,
							time_zone=tz)


		
		# ---- availability
		# -------- missing
		self.assertRaisesMessage(IntegrityError, "'availability' cannot be null", callable_obj=item_create, 
							user=user,
							name=u"错误物品6",
							description=u"正确",
							price=99,
							#availability=99,
							purchase_limit=1,
							expire_date=expire_date,
							event_start=event_start,
							time_zone=tz)

		# --------- out of range
		if DataError:
			self.assertRaisesMessage(DataError, "Out of range value for column 'availability'", callable_obj=item_create, 
							user=user,
							name=u"错误物品",
							description=u"正确",
							price=9,
							availability=-99,
							purchase_limit=11,
							expire_date=expire_date,
							event_start=event_start,
							time_zone=tz)	

		
		# ---- purchase limit
		# -------- missing
		item = item_create(user=user,
							name=u"错误物品",
							description=u"正确",
							price=99,
							availability=999,
							#purchase_limit=1,
							expire_date=expire_date,
							event_start=event_start,
							time_zone=tz)	

		self.assertEqual(item.purchase_limit, item.availability)

		item.delete()


		# --------purchase limit larger than availability
		item = item_create(user=user,
							name=u"错误物品",
							description=u"正确",
							price=99,
							availability=9,
							purchase_limit=200,
							expire_date=expire_date,
							event_start=event_start,
							time_zone=tz)

		self.assertEqual(item.purchase_limit, 200)

		item.delete()


		# --------purchase limit being negative
		if DataError:
			self.assertRaisesMessage(DataError, "Out of range value for column 'purchase_limit'", callable_obj=item_create, 
							user=user,
							name=u"错误物品",
							description=u"正确",
							price=9,
							availability=99,
							purchase_limit=-11,
							expire_date=expire_date,
							event_start=event_start,
							time_zone=tz)

		# ----dates
		# --------expire_date earlier than event_start
		# TODO: unicode message are not identified to be the same
		self.assertRaises(ValidationError, callable_obj=item_create, 
							user=user,
							name=u"错误物品",
							description=u"正确",
							price=9,
							availability=99,
							purchase_limit=11,
							expire_date=expire_date,
							event_start=expire_date - datetime.timedelta(hours=24),
							time_zone=tz)


	def test_event_item_availability(self):
		test_item = EventItem.objects.get(name__exact=u"测试活动")
		test_item.availability = 10
		test_item.save()
		self.assertEqual(test_item.availability, 10)

		# in range decrement
		status, test_item = EventItem.objects.decrement_item_availability(test_item, 2)
		self.assertEqual(status, True)
		self.assertEqual(test_item.availability, 8)

		# on limit decrement
		status, test_item = EventItem.objects.decrement_item_availability(test_item, 8)
		self.assertEqual(status, True)
		self.assertEqual(test_item.availability, 0)

		# over limit decrement
		status, test_item = EventItem.objects.decrement_item_availability(test_item, 1)
		self.assertEqual(status, False)
		self.assertEqual(test_item.availability, 0)

		status, test_item = EventItem.objects.increment_item_availability(test_item, 10)
		self.assertEqual(status, True)
		self.assertEqual(test_item.availability, 10)


	def test_generate_qrcontent(self):
		ticket_owner = User.objects.get(username__exact='olalalahao')
		test_event = EventItem.objects.get(name__exact=u'测试活动')

		# success creation
		ticket = test_event.generate_QRcontent(owner=ticket_owner, deliver_on_success=False)

		self.failIf(ticket==None)

		ticket = TicketPass.objects.get(pk=ticket.pk)

		self.assertEqual(ticket.owner_id, ticket_owner.id)
		self.assertEqual(ticket.distributor_id, test_event.user_id)
		self.assertEqual(ticket.title, test_event.name)
		self.assertEqual(ticket.time_zone, test_event.time_zone)

		# distributor and owner are the same person
		ticket = test_event.generate_QRcontent(owner=test_event.user, deliver_on_success=False)
		self.failIf(ticket!=None)

		# passed expire_date
		test_event.expire_date -= datetime.timedelta(hours=12)
		test_event.event_start -= datetime.timedelta(hours=12)
		#test_event.expire_date = datetime.datetime.now() # pass in timezone unaware values
		#test_event.expire_date.replace(tzinfo=pytz.UTC)
		#self.failUnless(djtimezone.is_aware(test_event.expire_date))
		test_event.save()
		ticket = test_event.generate_QRcontent(owner=ticket_owner, deliver_on_success=False)
		self.failIf(ticket!=None)

		# pass timezone unaware object

	def test_show_event_attenders(self):
		# create event:
		user = User.objects.get(username__exact='lalalalavic')
		tz = pytz.timezone('Asia/Shanghai')
		expire_date =  djtimezone.now().astimezone(tz) + datetime.timedelta(hours=12)
		event_start = expire_date + datetime.timedelta(hours=24)

		# 创建2个测试活动
		event_item_1 = EventItem.objects.create(user=user,
								name=u"测试120人活动1",
								description=u"活动1测试人员为100人",
								price=99,
								availability=120,
								purchase_limit=1,
								expire_date=expire_date,
								event_start=event_start,
								time_zone=tz)

		event_item_1 = EventItem.objects.get(name__exact=u"测试120人活动1")

		event_item_2 = EventItem.objects.create(user=user,
								name=u"测试120人活动2",
								description=u"活动2测试人员为120人",
								price=99,
								availability=120,
								purchase_limit=1,
								expire_date=expire_date,
								event_start=event_start,
								time_zone=tz)

		event_item_2 = EventItem.objects.get(name__exact=u"测试120人活动2")
		# create 100 attending event 1 users and 20 attending event 2 users
		for n in range(1, 21):
			user = User.objects.create_user(username="event1_attender%s" % n, 
									password="event1_attender%s" % n,
									email="zhang%s@illinois.edu" % n)
			user.is_active = True
			user.is_superuser = False
			user.is_staff = False
			user.save()

			event_item_1.generate_QRcontent(owner=user, deliver_on_success=False)
		for n in range(21, 41):
			user = User.objects.create_user(username="event2_attender%s" % n, 
									password="event2_attender%s" % n,
									email="zhang%s@illinois.edu" % n)
			user.is_active = True
			user.is_superuser = False
			user.is_staff = False
			user.save()

			event_item_2.generate_QRcontent(owner=user, deliver_on_success=False)


		event_1_attenders = event_item_1.show_event_attenders()
		event_2_attenders = event_item_2.show_event_attenders()

		for n in range(1, 41):
			if n <= 20:
				user = User.objects.get(username="event1_attender%s" % n)
				self.failUnless(user in event_1_attenders)
				self.failIf(user in event_2_attenders)
			else:
				user = User.objects.get(username="event2_attender%s" % n)
				self.failUnless(user in event_2_attenders)	
				self.failIf(user in event_1_attenders)






class PaybackFundTestCase(TestCase):

	def setUp(self):
		user = User.objects.create_user(username='paybackfund_tester', 
										password='paybackfund_tester', 
										email='zhang368@illinois.edu')
		user.is_active = True
		user.is_staff = False
		user.is_superuser = False
		user.save()

	def test_payback_fund_create(self):
		user = User.objects.get(username__exact='paybackfund_tester')

		pay_fund = PaybackFund.objects.create(user=user,
												name=u"正确普通筹资",
												description=u"正确",
												price=9,
												goal=999)

		pay_fund = PaybackFund.objects.get(name__exact=u"正确普通筹资")

		self.assertEqual(pay_fund.user_id, user.id)
		self.assertEqual(pay_fund.name, u"正确普通筹资")
		self.assertEqual(pay_fund.description, u"正确")
		self.assertEqual(pay_fund.price, 9)
		self.assertEqual(pay_fund.goal, 999)
		


class DonationFundTestCase(TestCase):

	def setUp(self):
		user = User.objects.create_user(username='donationfund_tester', 
										password='donationfund_tester', 
										email='zhang368@illinois.edu')
		user.is_active = True
		user.is_staff = False
		user.is_superuser = False
		user.save()

	def test_donation_fund_create(self):
		user = User.objects.get(username__exact='donationfund_tester')

		don_fund = DonationFund.objects.create(user=user,
												name=u"正确捐款",
												description=u"正确",
												price=9,
												goal=999)

		don_fund = DonationFund.objects.get(name__exact=u"正确捐款")

		self.assertEqual(don_fund.user_id, user.id)
		self.assertEqual(don_fund.name, u"正确捐款")
		self.assertEqual(don_fund.description, u"正确")
		self.assertEqual(don_fund.price, 9)
		self.assertEqual(don_fund.goal, 999)





