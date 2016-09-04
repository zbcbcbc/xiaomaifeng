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

from platforms.renren.models import RenrenClient, RenrenPost
from dashboard.listing.models import *

# Create your tests here.

logging.disable(logging.WARNING)




class RenrenClientTestCase(TestCase):

	def setUp(self):
		User.objects.create_user(username='rr_tester', password='rr_tester', email='zhang368@illinois.edu')

		rr_tester = User.objects.get(username='rr_tester')

		rr_tester.is_active = True
		rr_tester.is_superuser = False
		rr_tester.is_staff = False
		rr_tester.save()

		self.assertEqual(rr_tester.username, 'rr_tester')
		self.assertEqual(rr_tester.email, 'zhang368@illinois.edu')
		self.assertEqual(rr_tester.is_active, True)
		self.assertEqual(rr_tester.is_superuser, False)
		self.assertEqual(rr_tester.is_staff, False)


		User.objects.create_user(username='rr_tester2', password='rr_tester2', email='zhang368@illinois.edu')

		rr_tester = User.objects.get(username='rr_tester2')

		rr_tester.is_active = True
		rr_tester.is_superuser = False
		rr_tester.is_staff = False
		rr_tester.save()

		self.assertEqual(rr_tester.username, 'rr_tester2')
		self.assertEqual(rr_tester.email, 'zhang368@illinois.edu')
		self.assertEqual(rr_tester.is_active, True)
		self.assertEqual(rr_tester.is_superuser, False)
		self.assertEqual(rr_tester.is_staff, False)


	def test_renrenclient_create(self):
		rr_tester = User.objects.get(username='rr_tester')
		uid = 123456789 # self assigned value
		access_token = 987654321 # self assigned value
		user_name = 'olalalavic'
		expires_in = 123456 # in seconds


		# success creation
		rr_client = RenrenClient.objects.create(user=rr_tester, 
												uid=uid, 
												access_token=access_token,
												user_name=user_name,
												expires_in=expires_in)
		self.failUnless(rr_client)
		self.assertEqual(rr_client.user_id, rr_tester.id)
		self.assertEqual(rr_client.uid, uid)
		self.assertEqual(rr_client.access_token, access_token)
		self.assertEqual(rr_client.user_name, user_name)
		self.assertEqual(rr_client.username, None)
		self.assertEqual(rr_client.password, None)
		self.assertEqual(rr_client.refresh_token, None)
		self.assertEqual(rr_client.expires_in, expires_in)
		self.assertEqual(rr_client.visitor_count, 0)
		self.assertEqual(rr_client.friend_count, 0)
		self.failUnless(rr_client.add_date)

		renrenclient_create = RenrenClient.objects.create

		# no user
		self.assertRaisesMessage(IntegrityError, "Column 'user_id' cannot be null", callable_obj=renrenclient_create,
								uid=uid, access_token=access_token, user_name=user_name, expires_in=expires_in)


		# multille weibo client for single user
		self.assertRaisesMessage(IntegrityError, "Duplicate entry", callable_obj=renrenclient_create,
								user=rr_tester,
								uid=uid, 
								access_token=access_token, 
								user_name=user_name, 
								expires_in=expires_in)


		rr_client.delete()
		# missing uid
		self.assertRaisesMessage(IntegrityError, "Column 'uid' cannot be null", callable_obj=renrenclient_create,
								user=rr_tester,
								access_token=access_token, 
								user_name=user_name, 
								expires_in=expires_in)		

		# ---- bad uid
		bad_uid = 9223372036854775808 # big integer (64) overflow
		self.assertRaisesMessage(DataError, "Out of range value for column 'uid'", callable_obj=renrenclient_create,
								user=rr_tester,
								uid=bad_uid,
								access_token=access_token, 
								user_name=user_name, 
								expires_in=expires_in)	

		# ---- none unique uid
		rr_client = RenrenClient.objects.create(user=rr_tester, 
												uid=uid, 
												access_token=access_token,
												user_name=user_name,
												expires_in=expires_in)

		rr_tester2 = User.objects.get(username='rr_tester2')
		self.assertRaisesMessage(IntegrityError, "Duplicate entry", callable_obj=renrenclient_create,
								user=rr_tester2,
								uid=uid,
								access_token=access_token, 
								user_name=user_name, 
								expires_in=expires_in)	

		rr_client.delete()	



	def test_get_unique_or_none(self):
		rr_tester = User.objects.get(username='rr_tester')
		uid = 123456789 # self assigned value
		access_token = 987654321 # self assigned value
		user_name = 'olalalavic'
		expires_in = 123456 # in seconds

		rr_client = RenrenClient.objects.create(user=rr_tester, 
												uid=uid, 
												access_token=access_token,
												user_name=user_name,
												expires_in=expires_in)

		_rr_client = RenrenClient.objects.get_unique_or_none(user=rr_tester)
		self.failUnless(_rr_client)

		_rr_client.delete()

		rr_tester = RenrenClient.objects.get_unique_or_none(user=rr_tester)
		self.failIf(rr_tester)		


	def test_update_priority(self):
		rr_tester = User.objects.get(username='rr_tester')
		uid = 123456789 # self assigned value
		access_token = 987654321 # self assigned value
		user_name = 'olalalavic'
		expires_in = 123456 # in seconds


		# success creation
		rr_client = RenrenClient.objects.create(user=rr_tester, 
												uid=uid, 
												access_token=access_token,
												user_name=user_name,
												expires_in=expires_in)
		self.assertEqual(rr_client.priority, 1)	

		rr_client.friend_count = 1
		rr_client.visitor_count = 1
		rr_client.update_priority(write_to_db=True)
		self.assertEqual(rr_client.priority, 0)		
		

		rr_client.friend_count = 500000
		rr_client.visitor_count = 50000
		rr_client.update_priority(write_to_db=True)
		self.assertEqual(rr_client.priority, 2)	


class RenrenTestCase(TestCase):

	def setUp(self):
		"""
		Initiate user, renren_client, content
		"""
		User.objects.create_user(username='rr_p_tester', password='rr_p_tester', email='zhang368@illinois.edu')

		rr_p_tester = User.objects.get(username='rr_p_tester')

		rr_p_tester.is_active = True
		rr_p_tester.is_superuser = False
		rr_p_tester.is_staff = False
		rr_p_tester.save()		

		uid = 123456789 # self assigned value
		access_token = 987654321 # self assigned value
		user_name = 'olalalavic'
		expires_in = 123456 # in seconds

		rr_p_client = RenrenClient.objects.create(user=rr_p_tester, 
												uid=uid, 
												access_token=access_token,
												user_name=user_name,
												expires_in=expires_in,
												priority=1)	

		PhysicalItem.objects.create(user=rr_p_tester,
							name=u"测试renrenpost物品",
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

		event_item = EventItem.objects.create(user=rr_p_tester,
								name=u"测试renrenpost活动",
								description=u"正确的活动用来测试",
								price=99,
								availability=99,
								purchase_limit=1,
								expire_date=expire_date,
								event_start=event_start,
								time_zone=tz)

		pay_fund = PaybackFund.objects.create(user=rr_p_tester,
												name=u"测试renrenpost普通筹资",
												description=u"正确",
												price=9,
												goal=999)

		don_fund = DonationFund.objects.create(user=rr_p_tester,
												name=u"测试renrenpost捐款",
												description=u"正确",
												price=9,
												goal=999)


	def test_renrenpost_create(self):
		rr_p_tester = User.objects.get(username='rr_p_tester')
		rr_p_client = RenrenClient.objects.get(user=rr_p_tester)
		phy_item = PhysicalItem.objects.get(name__exact=u"测试renrenpost物品")

		# success creation with different content
		# ---- with physical item
		RenrenPost.objects.create(client=rr_p_client,
									content_object=phy_item,
									uid=rr_p_client.uid,
									pid=1234567,
									text=u"测试用的renrenpost",
									priority=rr_p_client.priority)

		renren_post = RenrenPost.objects.get(client=rr_p_client, pid=1234567)

		self.assertEqual(renren_post.client_id, rr_p_client.pk)
		self.assertEqual(renren_post.uid, rr_p_client.uid)
		self.assertEqual(renren_post.pid, u"1234567")
		self.assertEqual(renren_post.text, u"测试用的renrenpost")
		self.assertEqual(renren_post.content_object, phy_item)
		self.assertEqual(renren_post.priority, rr_p_client.priority)


		# ---- with digital item TODO
		# ---- with event item
		eve_item = EventItem.objects.get(name__exact=u"测试renrenpost活动")
		RenrenPost.objects.create(client=rr_p_client,
									content_object=eve_item,
									uid=rr_p_client.uid,
									pid=1234568,
									text=u"测试用的renrenpost",
									priority=rr_p_client.priority)

		renren_post = RenrenPost.objects.get(client=rr_p_client, pid=1234568)

		self.assertEqual(renren_post.client_id, rr_p_client.pk)
		self.assertEqual(renren_post.uid, rr_p_client.uid)
		self.assertEqual(renren_post.pid, u"1234568")
		self.assertEqual(renren_post.text, u"测试用的renrenpost")
		self.assertEqual(renren_post.content_object, eve_item)
		self.assertEqual(renren_post.priority, rr_p_client.priority)

		# ---- with payback fund
		pay_fund = PaybackFund.objects.get(name__exact=u"测试renrenpost普通筹资")
		RenrenPost.objects.create(client=rr_p_client,
									content_object=pay_fund,
									uid=rr_p_client.uid,
									pid=1234569,
									text=u"测试用的renrenpost",
									priority=rr_p_client.priority)

		renren_post = RenrenPost.objects.get(client=rr_p_client, pid=1234569)

		self.assertEqual(renren_post.client_id, rr_p_client.pk)
		self.assertEqual(renren_post.uid, rr_p_client.uid)
		self.assertEqual(renren_post.pid, u"1234569")
		self.assertEqual(renren_post.text, u"测试用的renrenpost")
		self.assertEqual(renren_post.content_object, pay_fund)
		self.assertEqual(renren_post.priority, rr_p_client.priority)	

		# ---- with donation fund
		don_fund = DonationFund.objects.get(name__exact=u"测试renrenpost捐款")
		RenrenPost.objects.create(client=rr_p_client,
									content_object=don_fund,
									uid=rr_p_client.uid,
									pid=1234570,
									text=u"测试用的renrenpost",
									priority=rr_p_client.priority)

		renren_post = RenrenPost.objects.get(client=rr_p_client, pid=1234570)

		self.assertEqual(renren_post.client_id, rr_p_client.pk)
		self.assertEqual(renren_post.uid, rr_p_client.uid)
		self.assertEqual(renren_post.pid, u"1234570")
		self.assertEqual(renren_post.text, u"测试用的renrenpost")
		self.assertEqual(renren_post.content_object, don_fund)
		self.assertEqual(renren_post.priority, rr_p_client.priority)				


		renrenpost_create = RenrenPost.objects.create
		# fail creation -- missing client
		self.assertRaisesMessage(IntegrityError, "Column 'client_id' cannot be null", callable_obj=renrenpost_create,
									content_object=phy_item,
									uid=rr_p_client.uid,
									pid=1234567,
									text=u"错误的renrenpost",
									priority=rr_p_client.priority)

		# missing content_object
		self.assertRaisesMessage(IntegrityError, "Column 'content_type_id' cannot be null", callable_obj=renrenpost_create,
									client=rr_p_client,
									uid=rr_p_client.uid,
									pid=1234567,
									text=u"错误的renrenpost",
									priority=rr_p_client.priority)	

		# missing uid
		self.assertRaisesMessage(IntegrityError, "Column 'uid' cannot be null", callable_obj=renrenpost_create,
									client=rr_p_client,
									content_object=phy_item,
									pid=1234567,
									text=u"错误的renrenpost",
									priority=rr_p_client.priority)	

		# duplicate item
		self.assertRaisesMessage(IntegrityError, "Column 'client_id' cannot be null", callable_obj=renrenpost_create,
									content_object=phy_item,
									uid=rr_p_client.uid,
									pid=1234567,
									text=u"错误的renrenpost",
									priority=rr_p_client.priority)


	def test_update_priority(self):
		pass

	