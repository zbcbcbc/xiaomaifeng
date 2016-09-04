# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError

from models import UserProfile, UserGroup, Membership

# Create your tests here.



class UserProfileTestCase(TestCase):

	def setUp(self):
		pass

	def test_userprofile_create(self):
		"""
		When user is created, a signal is sent to create user profile
		"""
		user = User.objects.create_user(username='test_profile_create_user', 
										password='olalalalalalala',
										first_name='congming',
										last_name='xiaohuang',
										email='xiaohuang@gmail.com')

		user_profile = user.userprofile
		# -- creation check and primary key check
		self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)
		self.assertEqual(user.pk, user_profile.pk)

		# -- Testing Essential Attributes 

		user_profile_save = user_profile.save

		# ---- address_1 
		# -------- overlength limit 128 char
		"""
		#TODO: expect DataError

		user_profile.address_1 = u'测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数\
									测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数\
									测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数\
									测试数量超过限制字数测试数量超过限制字数'
		self.assertRaisesMessage(IntegrityError, 'lalala', user_profile_save)

		"""

		# ---- address_2
		# --------- overlength limit 64 char
		"""
		#TODO: expect DataError

		user_profile.address_2 = u'测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数\
									测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数\
									测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数测试数量超过限制字数\
									测试数量超过限制字数测试数量超过限制字数'
		self.assertRaisesMessage(IntegrityError, 'lalala', user_profile_save)

		"""	

		# ---- province
		# --------- selection error

		"""
		#TODO: IntegrityError not raised for selection model fields

		user_profile.province = 'lalala'
		self.assertRaisesMessage(IntegrityError, 'lalala', user_profile_save)

		"""

		# ---- zip_code
		# -------- random strings
		"""
		user_profile.zip_code = 'lalalalala'
		#self.assertRaisesMessage(IntegrityError, 'lalala', user_profile_save)	
		"""

		# ---- mobile
		# -------- random strings
		"""
		user_profile.mobile = 'lalalalala'
		#self.assertRaisesMessage(IntegrityError, 'lalala', user_profile_save)	
		"""





class MembershipTestCase(TestCase):

	def setUp(self):
		pass


	def test_membership_create(self):
		"""
		测试建立Membership是否正确
		"""
		pass


	def test_user_is_premium(self):
		"""
		测试监测用户是否是高级会员方法
		"""
		pass


	def test_user_is_enterprise(self):
		"""
		测试监测用户是否是企业会员方法
		"""
		pass

	def test_membership_expires(self):
		"""
		测试用户会员是否过期方法
		"""
		pass

	def test_handle_expired_membership(self):
		"""
		测试处理过期用户Membership方法
		"""
		pass





















