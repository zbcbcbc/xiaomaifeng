# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging, datetime, pytz

from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.test.client import Client

from siteutils.testhelpers import profile as time_profile
from dashboard.listing.models import PhysicalItem, DigitalItem, PaybackFund, DonationFund, EventItem
from dashboard.listing.views import *
from dashboard.passbook.models import TicketPass


logging.disable(logging.WARNING)


class ItemListViewTestCase(TestCase):

	def setUp(self):
		user = User.objects.create_user(username='itemview_tester', password='itemview_tester', email='zhang368@illinois.edu')
		user.is_active = True
		user.is_staff = False
		user.is_superuser = False
		user.save()

		self.client = Client()
		self.client.login(username='itemview_tester', password='itemview_tester')


	def test_itemlistview_login(self):
		self.client.logout()		
		resp = self.client.get('/dashboard/listing/itemlist/')
		self.assertEqual(resp.status_code, 302)

		resp = self.client.get('/dashboard/listing/itemlist/', follow=True)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.template_name, 'accounts/login.html')

		self.client.login(username='itemview_tester', password='itemview_tester')
		resp = self.client.get('/dashboard/listing/itemlist/')
		self.assertEqual(resp.status_code, 200)		


	def test_itemlistview(self):
		"""
		测试ItemListView返回的context
		"""
		# 测试实体物品是否出现在列表
		user = User.objects.get(username__exact='itemview_tester')
		phy_item = PhysicalItem.objects.create(user=user,
							name=u"正确物品",
							description=u"正确",
							price=99,
							availability=99,
							purchase_limit=1,
							logistics_fee=10)
		resp = self.client.get('/dashboard/listing/itemlist/')
		self.assertEqual(resp.status_code, 200)
		items = resp.context['items']
		self.failUnless(phy_item in items)
		self.failUnless(phy_item.name.encode('utf-8') in resp.content)


		#TODO: 测试虚拟物品是否出现在列表

		#  测试活动物品是否出现在列表
		tz = pytz.timezone('Asia/Shanghai')
		expire_date = datetime.datetime.now().replace(tzinfo=tz)
		event_start = expire_date + datetime.timedelta(hours=12)
		eve_item = EventItem.objects.create(user=user,
							name=u"正确活动",
							description=u"正确",
							price=99,
							availability=99,
							purchase_limit=1,
							expire_date=expire_date,
							event_start=event_start,
							time_zone=tz)
		resp = self.client.get('/dashboard/listing/itemlist/')
		self.assertEqual(resp.status_code, 200)
		items = resp.context['items']
		self.failUnless(eve_item in items)
		self.failUnless(phy_item in items)
		self.failUnless(eve_item.name.encode('utf-8') in resp.content)
		self.failUnless(phy_item.name.encode('utf-8') in resp.content)

		phy_item.delete()
		eve_item.delete()


		# 非用户用户物品
		user2 = User.objects.create_user(username='itemview_tester2', password='itemview_tester2', email='zhang368@illinois.edu')
		user2.is_active = True
		user2.is_staff = False
		user2.is_superuser = False
		user2.save()

		# ---- 实体物品
		phy_item = PhysicalItem.objects.create(user=user2,
							name=u"正确物品",
							description=u"正确",
							price=99,
							availability=99,
							purchase_limit=1,
							logistics_fee=10)

		resp = self.client.get('/dashboard/listing/itemlist/')
		self.assertEqual(resp.status_code, 200)
		items = resp.context['items']
		self.failIf(phy_item in items)	
		self.failIf(phy_item.name.encode('utf-8') in resp.content)	


		# ---- TODO: 虚拟物品
		# ---- 活动物品
		tz = pytz.timezone('Asia/Shanghai')
		expire_date = datetime.datetime.now().replace(tzinfo=tz)
		event_start = expire_date + datetime.timedelta(hours=12)
		eve_item = EventItem.objects.create(user=user2,
							name=u"正确活动",
							description=u"正确",
							price=99,
							availability=99,
							purchase_limit=1,
							expire_date=expire_date,
							event_start=event_start,
							time_zone=tz)

		resp = self.client.get('/dashboard/listing/itemlist/')
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.template_name, ['listing/itemlist.html'])
		items = resp.context['items']
		self.failIf(eve_item in items)	
		self.failIf(eve_item.name.encode('utf-8') in resp.content)	


	def test_itemlistview_cache(self):
		pass

	"""
	@time_profile
	def test_itemlistview_load_iteration(self):
		import time
		# prepare data
		TEST_WATERMARK = 10000
		itemview_tester = User.objects.get(username__exact='itemview_tester')
		itemview_tester2 = User.objects.get(username__exact='lalalalavic')
		self.client.login(username='itemview_tester', password='itemview_tester')
		count = 0

		# create items
		create_item_start_time = time.time()
		while count < TEST_WATERMARK:
			PhysicalItem.objects.create(user=itemview_tester,
										name=self._generate_item_name(),
										description=u"非常长的描写读取时间非常长的描写读取时间非常长的描写读取时间", # description is pretty short
										price=99,
										availability=99,
										purchase_limit=1,
										logistics_fee=10)

			PhysicalItem.objects.create(user=itemview_tester2,
										name=self._generate_item_name(),
										description=u"非常长的描写读取时间非常长的描写读取时间非常长的描写读取时间", # description is pretty short
										price=99,
										availability=99,
										purchase_limit=1,
										logistics_fee=10)

			count += 1
		print u"创建 %s件物品耗时: %s秒" % (TEST_WATERMARK, time.time() - create_item_start_time)

		read_item_start_time = time.time()
		resp = self.client.get('/dashboard/listing/itemlist/')
		items = resp.context['items']
		print u"读取 %s件物品耗时: %s秒" % (TEST_WATERMARK, time.time() - read_item_start_time)

		iterate_item_start_time = time.time()
		for item in items:
			item.user.id
		print u"Iterate %s件物品耗时: %s秒" % (TEST_WATERMARK, time.time() - iterate_item_start_time)
	"""
			



	def _generate_item_name(self):
		import uuid
		return str(uuid.uuid4())



		


		#print resp

class FundListViewTestCase(TestCase):

	def setUp(self):
		user = User.objects.create_user(username='fundview_tester', password='fundview_tester', email='zhang368@illinois.edu')
		user.is_active = True
		user.is_staff = False
		user.is_superuser = False
		user.save()

		self.client = Client()
		self.client.login(username='fundview_tester', password='fundview_tester')


	def test_fundlistview_login(self):
		self.client.logout()		
		resp = self.client.get('/dashboard/listing/fundlist/')
		self.assertEqual(resp.status_code, 302)

		resp = self.client.get('/dashboard/listing/fundlist/', follow=True)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.template_name, 'accounts/login.html')


		self.client.login(username='fundview_tester', password='fundview_tester')
		resp = self.client.get('/dashboard/listing/fundlist/')
		self.assertEqual(resp.status_code, 200)		
		self.assertEqual(resp.template_name, ['listing/fundlist.html'])



	def test_fundlistview(self):
		"""
		测试ItemListView返回的context
		"""
		# 测试普通筹资是否出现在列表
		user = User.objects.get(username__exact='fundview_tester')
		pay_fund = PaybackFund.objects.create(user=user,
							name=u"正确筹资",
							description=u"正确",
							price=99,
							goal=999)
		resp = self.client.get('/dashboard/listing/fundlist/')
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.template_name, ['listing/fundlist.html'])
		funds = resp.context['funds']
		self.failUnless(pay_fund in funds)
		self.failUnless(pay_fund.name.encode('utf-8') in resp.content)


		#  测试捐款筹资是否出现在列表
		don_fund = DonationFund.objects.create(user=user,
							name=u"正确筹资",
							description=u"正确",
							price=99,
							goal=99)
		resp = self.client.get('/dashboard/listing/fundlist/')
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.template_name, ['listing/fundlist.html'])
		funds = resp.context['funds']
		self.failUnless(don_fund in funds)
		self.failUnless(don_fund.name.encode('utf-8') in resp.content)	


		pay_fund.delete()
		don_fund.delete()


		# 非用户用户物品
		user2 = User.objects.create_user(username='fundview_tester2', password='fundview_tester2', email='zhang368@illinois.edu')
		user2.is_active = True
		user2.is_staff = False
		user2.is_superuser = False
		user2.save()

		# ---- 普通筹资
		pay_fund = PaybackFund.objects.create(user=user2,
							name=u"正确筹资",
							description=u"正确",
							price=99,
							goal=999)

		resp = self.client.get('/dashboard/listing/fundlist/')
		self.assertEqual(resp.status_code, 200)
		funds = resp.context['funds']
		self.failIf(pay_fund in funds)
		self.failIf(pay_fund.name.encode('utf-8') in resp.content)		

		# ----  捐款筹资
		don_fund = DonationFund.objects.create(user=user2,
							name=u"正确活动",
							description=u"正确",
							price=99,
							goal=999)

		resp = self.client.get('/dashboard/listing/fundlist/')
		self.assertEqual(resp.status_code, 200)
		funds = resp.context['funds']
		self.failIf(don_fund in funds)
		self.failIf(don_fund.name.encode('utf-8') in resp.content)	




class CreatePhysicalItemViewTestCase(TestCase):

	def setUp(self):
		user = User.objects.create_user(username='create_physicalitem_tester', 
										password='create_physicalitem_tester', 
										email='zhang368@illinois.edu')
		user.is_active = True
		user.is_staff = False
		user.is_superuser = False
		user.save()

		self.client = Client()
		self.client.login(username='create_physicalitem_tester', password='create_physicalitem_tester')


	def test_createitemview_login(self):
		self.client.logout()		
		resp = self.client.get('/dashboard/listing/additem/physical/')
		self.assertEqual(resp.status_code, 302)

		resp = self.client.get('/dashboard/listing/additem/physical', follow=True)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp.template_name, 'accounts/login.html')

		self.client.login(username='create_physicalitem_tester', password='create_physicalitem_tester')
		resp = self.client.get('/dashboard/listing/additem/physical/')
		self.assertEqual(resp.status_code, 200)	






