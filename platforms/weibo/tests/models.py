# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging, datetime, pytz

from django.utils import timezone as djtimezone
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError, DataError
from django.core.exceptions import ValidationError

from dashboard.listing.models import *
from platforms.weibo.models import WeiboClient, WeiboPost

# Create your tests here.

logging.disable(logging.WARNING)




class WeiboClientTestCase(TestCase):

	def setUp(self):
		User.objects.create_user(username='wb_tester', password='wb_tester', email='zhang368@illinois.edu')

		wb_tester = User.objects.get(username='wb_tester')

		wb_tester.is_active = True
		wb_tester.is_superuser = False
		wb_tester.is_staff = False
		wb_tester.save()

		self.assertEqual(wb_tester.username, 'wb_tester')
		self.assertEqual(wb_tester.email, 'zhang368@illinois.edu')
		self.assertEqual(wb_tester.is_active, True)
		self.assertEqual(wb_tester.is_superuser, False)
		self.assertEqual(wb_tester.is_staff, False)


		User.objects.create_user(username='wb_tester2', password='wb_tester2', email='zhang368@illinois.edu')

		wb_tester = User.objects.get(username='wb_tester2')

		wb_tester.is_active = True
		wb_tester.is_superuser = False
		wb_tester.is_staff = False
		wb_tester.save()

		self.assertEqual(wb_tester.username, 'wb_tester2')
		self.assertEqual(wb_tester.email, 'zhang368@illinois.edu')
		self.assertEqual(wb_tester.is_active, True)
		self.assertEqual(wb_tester.is_superuser, False)
		self.assertEqual(wb_tester.is_staff, False)


	def test_weiboclient_create(self):
		wb_tester = User.objects.get(username='wb_tester')
		uid = 123456789 # self assigned value
		access_token = 987654321 # self assigned value
		user_name = 'olalalavic'
		expires_in = 123456 # in seconds


		# success creation
		wb_client = WeiboClient.objects.create(user=wb_tester, 
												uid=uid, 
												access_token=access_token,
												user_name=user_name,
												expires_in=expires_in)
		self.failUnless(wb_client)
		self.assertEqual(wb_client.user_id, wb_tester.id)
		self.assertEqual(wb_client.uid, uid)
		self.assertEqual(wb_client.access_token, access_token)
		self.assertEqual(wb_client.user_name, user_name)
		self.assertEqual(wb_client.username, None)
		self.assertEqual(wb_client.password, None)
		self.assertEqual(wb_client.refresh_token, None)
		self.assertEqual(wb_client.expires_in, expires_in)
		self.assertEqual(wb_client.followers_count, 0)
		self.assertEqual(wb_client.friends_count, 0)
		self.assertEqual(wb_client.priority, 1) # default priority
		self.failUnless(wb_client.add_date)

		weiboclient_create = WeiboClient.objects.create

		# no user
		self.assertRaisesMessage(IntegrityError, "Column 'user_id' cannot be null", callable_obj=weiboclient_create,
								uid=uid, access_token=access_token, user_name=user_name, expires_in=expires_in)


		# multille weibo client for single user
		self.assertRaisesMessage(IntegrityError, "Duplicate entry", callable_obj=weiboclient_create,
								user=wb_tester,
								uid=uid, 
								access_token=access_token, 
								user_name=user_name, 
								expires_in=expires_in,
								priority=1)


		wb_client.delete()
		# missing uid
		self.assertRaisesMessage(IntegrityError, "Column 'uid' cannot be null", callable_obj=weiboclient_create,
								user=wb_tester,
								access_token=access_token, 
								user_name=user_name, 
								expires_in=expires_in,
								priority=1)		

		# ---- bad uid
		bad_uid = 9223372036854775808 # big integer (64) overflow
		self.assertRaisesMessage(DataError, "Out of range value for column 'uid'", callable_obj=weiboclient_create,
								user=wb_tester,
								uid=bad_uid,
								access_token=access_token, 
								user_name=user_name, 
								expires_in=expires_in,
								priority=1)	


		# out of balance priority
		self.assertRaisesMessage(DataError, "Data too long for column 'priority'", callable_obj=weiboclient_create,
								user=wb_tester,
								uid=uid,
								access_token=access_token, 
								user_name=user_name, 
								expires_in=expires_in,
								priority=12)	

		# ---- none unique uid
		wb_client = WeiboClient.objects.create(user=wb_tester, 
												uid=uid, 
												access_token=access_token,
												user_name=user_name,
												expires_in=expires_in,
												priority=1)

		wb_tester2 = User.objects.get(username='wb_tester2')
		self.assertRaisesMessage(IntegrityError, "Duplicate entry", callable_obj=weiboclient_create,
								user=wb_tester2,
								uid=uid,
								access_token=access_token, 
								user_name=user_name, 
								expires_in=expires_in,
								priority=1)	

		wb_client.delete()	



	def test_get_unique_or_none(self):
		wb_tester = User.objects.get(username='wb_tester')
		uid = 123456789 # self assigned value
		access_token = 987654321 # self assigned value
		user_name = 'olalalavic'
		expires_in = 123456 # in seconds

		wb_client = WeiboClient.objects.create(user=wb_tester, 
												uid=uid, 
												access_token=access_token,
												user_name=user_name,
												expires_in=expires_in)

		_wb_client = WeiboClient.objects.get_unique_or_none(user=wb_tester)
		self.failUnless(_wb_client)

		_wb_client.delete()

		wb_tester = WeiboClient.objects.get_unique_or_none(user=wb_tester)
		self.failIf(wb_tester)	


	def test_update_priority(self):
		wb_tester = User.objects.get(username='wb_tester')
		uid = 123456789 # self assigned value
		access_token = 987654321 # self assigned value
		user_name = 'olalalavic'
		expires_in = 123456 # in seconds


		# success creation
		wb_client = WeiboClient.objects.create(user=wb_tester, 
												uid=uid, 
												access_token=access_token,
												user_name=user_name,
												expires_in=expires_in)
		self.assertEqual(wb_client.priority, 1)	

		wb_client.friends_count = 1
		wb_client.followers_count = 1
		wb_client.update_priority(write_to_db=True)
		self.assertEqual(wb_client.priority, 0)		
		

		wb_client.friends_count = 500000
		wb_client.followers_count = 50000
		wb_client.update_priority(write_to_db=True)
		self.assertEqual(wb_client.priority, 2)				





class WeiboPostTestCase(TestCase):

	def setUp(self):
		"""
		Initiate user, weibo_client, content
		"""
		User.objects.create_user(username='wb_p_tester', password='wb_p_tester', email='zhang368@illinois.edu')

		wb_p_tester = User.objects.get(username='wb_p_tester')

		wb_p_tester.is_active = True
		wb_p_tester.is_superuser = False
		wb_p_tester.is_staff = False
		wb_p_tester.save()		

		uid = 123456789 # self assigned value
		access_token = 987654321 # self assigned value
		user_name = 'olalalavic'
		expires_in = 123456 # in seconds

		wb_p_client = WeiboClient.objects.create(user=wb_p_tester, 
												uid=uid, 
												access_token=access_token,
												user_name=user_name,
												expires_in=expires_in,
												priority=1)	

		PhysicalItem.objects.create(user=wb_p_tester,
							name=u"测试weibopost物品",
							description=u"正确",
							price=99,
							availability=99,
							purchase_limit=1,
							logistics_fee=10)

		tz = pytz.timezone('Asia/Shanghai')
		expire_date =  djtimezone.now().astimezone(tz) + datetime.timedelta(hours=12)
		event_start = expire_date + datetime.timedelta(hours=24)

		#print 'expire_date', expire_date
		#print 'expire_date to store in db is aware?:', djtimezone.is_aware(expire_date)

		event_item = EventItem.objects.create(user=wb_p_tester,
								name=u"测试weibopost活动",
								description=u"正确的活动用来测试",
								price=99,
								availability=99,
								purchase_limit=1,
								expire_date=expire_date,
								event_start=event_start,
								time_zone=tz)

		pay_fund = PaybackFund.objects.create(user=wb_p_tester,
												name=u"测试weibopost普通筹资",
												description=u"正确",
												price=9,
												goal=999)

		don_fund = DonationFund.objects.create(user=wb_p_tester,
												name=u"测试weibopost捐款",
												description=u"正确",
												price=9,
												goal=999)

	def test_weibopost_create(self):
		wb_p_tester = User.objects.get(username='wb_p_tester')
		wb_p_client = WeiboClient.objects.get(user=wb_p_tester)
		phy_item = PhysicalItem.objects.get(name__exact=u"测试weibopost物品")

		# success creation with different content
		# ---- with physical item
		WeiboPost.objects.create(client=wb_p_client,
									content_object=phy_item,
									uid=wb_p_client.uid,
									pid=1234567,
									text=u"测试用的weibopost",
									priority=wb_p_client.priority)

		weibo_post = WeiboPost.objects.get(client=wb_p_client, pid=1234567)

		self.assertEqual(weibo_post.client_id, wb_p_client.pk)
		self.assertEqual(weibo_post.uid, wb_p_client.uid)
		self.assertEqual(weibo_post.pid, u"1234567")
		self.assertEqual(weibo_post.text, u"测试用的weibopost")
		self.assertEqual(weibo_post.content_object, phy_item)
		self.assertEqual(weibo_post.priority, wb_p_client.priority)


		# ---- with digital item TODO
		# ---- with event item
		eve_item = EventItem.objects.get(name__exact=u"测试weibopost活动")
		WeiboPost.objects.create(client=wb_p_client,
									content_object=eve_item,
									uid=wb_p_client.uid,
									pid=1234568,
									text=u"测试用的weibopost",
									priority=wb_p_client.priority)

		weibo_post = WeiboPost.objects.get(client=wb_p_client, pid=1234568)

		self.assertEqual(weibo_post.client_id, wb_p_client.pk)
		self.assertEqual(weibo_post.uid, wb_p_client.uid)
		self.assertEqual(weibo_post.pid, u"1234568")
		self.assertEqual(weibo_post.text, u"测试用的weibopost")
		self.assertEqual(weibo_post.content_object, eve_item)
		self.assertEqual(weibo_post.priority, wb_p_client.priority)

		# ---- with payback fund
		pay_fund = PaybackFund.objects.get(name__exact=u"测试weibopost普通筹资")
		WeiboPost.objects.create(client=wb_p_client,
									content_object=pay_fund,
									uid=wb_p_client.uid,
									pid=1234569,
									text=u"测试用的weibopost",
									priority=wb_p_client.priority)

		weibo_post = WeiboPost.objects.get(client=wb_p_client, pid=1234569)

		self.assertEqual(weibo_post.client_id, wb_p_client.pk)
		self.assertEqual(weibo_post.uid, wb_p_client.uid)
		self.assertEqual(weibo_post.pid, u"1234569")
		self.assertEqual(weibo_post.text, u"测试用的weibopost")
		self.assertEqual(weibo_post.content_object, pay_fund)
		self.assertEqual(weibo_post.priority, wb_p_client.priority)	

		# ---- with donation fund
		don_fund = DonationFund.objects.get(name__exact=u"测试weibopost捐款")
		WeiboPost.objects.create(client=wb_p_client,
									content_object=don_fund,
									uid=wb_p_client.uid,
									pid=1234570,
									text=u"测试用的weibopost",
									priority=wb_p_client.priority)

		weibo_post = WeiboPost.objects.get(client=wb_p_client, pid=1234570)

		self.assertEqual(weibo_post.client_id, wb_p_client.pk)
		self.assertEqual(weibo_post.uid, wb_p_client.uid)
		self.assertEqual(weibo_post.pid, u"1234570")
		self.assertEqual(weibo_post.text, u"测试用的weibopost")
		self.assertEqual(weibo_post.content_object, don_fund)
		self.assertEqual(weibo_post.priority, wb_p_client.priority)				


		weibopost_create = WeiboPost.objects.create
		# fail creation -- missing client
		self.assertRaisesMessage(IntegrityError, "Column 'client_id' cannot be null", callable_obj=weibopost_create,
									content_object=phy_item,
									uid=wb_p_client.uid,
									pid=1234567,
									text=u"错误的weibopost",
									priority=wb_p_client.priority)

		# missing content_object
		self.assertRaisesMessage(IntegrityError, "Column 'content_type_id' cannot be null", callable_obj=weibopost_create,
									client=wb_p_client,
									uid=wb_p_client.uid,
									pid=1234567,
									text=u"错误的weibopost",
									priority=wb_p_client.priority)	

		# missing uid
		self.assertRaisesMessage(IntegrityError, "Column 'uid' cannot be null", callable_obj=weibopost_create,
									client=wb_p_client,
									content_object=phy_item,
									pid=1234567,
									text=u"错误的weibopost",
									priority=wb_p_client.priority)	

		# duplicate item
		self.assertRaisesMessage(IntegrityError, "Column 'client_id' cannot be null", callable_obj=weibopost_create,
									content_object=phy_item,
									uid=wb_p_client.uid,
									pid=1234567,
									text=u"错误的weibopost",
									priority=wb_p_client.priority)


	def test_post_select_for_update(self):
		"""
		Determine if lock is needed when iterating posts
		"""
		pass

	