# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging, pytz, datetime

from django.utils import timezone as djtimezone
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError, DataError

from dashboard.profile.models import UserProfile, Membership, UserGroup

logging.disable(logging.ERROR)


class UserProfileTestCase(TestCase):

	def setUp(self):
		user = User.objects.create_user(username='ihavenoprofile', 
								password='ihavenoprofile', 
								email='zhang368@illinois.edu')

		user.is_active = True
		user.is_superuser = False
		user.is_staff = False

		user.save()

		self.assertEqual(user.username, 'ihavenoprofile')
		self.assertEqual(user.email, 'zhang368@illinois.edu')
		self.assertEqual(user.is_active, True)
		self.assertEqual(user.is_superuser, False)
		self.assertEqual(user.is_staff, False)


	def test_userprofile_create(self):
		user_no_profile = User.objects.get(username__exact='ihavenoprofile')

		# successful creation
		user_profile = UserProfile.objects.create(user=user_no_profile)
		self.assertEqual(user_profile.user_id, user_no_profile.id)
		self.failIf(user_profile.in_foreign)

		# duplicate user profile for singal user
		userprofile_create = UserProfile.objects.create

		self.assertRaisesMessage(IntegrityError, "Duplicate entry", callable_obj=userprofile_create, 
								user=user_no_profile)

		user_profile.delete()
		# model fields
		# -- address 1 length overflow (>128)
		self.assertRaisesMessage(DataError, "Data too long for column 'address_1'", callable_obj=userprofile_create, 
								user=user_no_profile,
								address_1=u"这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串\
									这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串\
									这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串\
									这是个十个字的字符") # 129
		# -- address 2 length overflow (>64)
		self.assertRaisesMessage(DataError, "Data too long for column 'address_2'", callable_obj=userprofile_create, 
								user=user_no_profile,
								address_2=u"这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串\
									这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串\
									这是个十个字的字符串这是个十个") # 65

		# -- provicne length overflow (>100)
		self.assertRaisesMessage(DataError, "Data too long for column 'province'", callable_obj=userprofile_create, 
								user=user_no_profile,
								province=u"这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串\
									这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串\
									这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串这是个十个字的字符串\
									这是个十个字的字符") # 129
		# -- country length overflow (>10)
		self.assertRaisesMessage(DataError, "Data too long for column 'country'", callable_obj=userprofile_create, 
								user=user_no_profile,
								country=u"这是个十个字的字符串这") # 11

		# -- zip code length overflow (>20)
		self.assertRaisesMessage(DataError, "Data too long for column 'zip_code'", callable_obj=userprofile_create, 
								user=user_no_profile,
								zip_code=u"这是个十个字的字符串这是个十个字的字符串这") # 21


		# -- mobile length overflow (>20)
		self.assertRaisesMessage(DataError, "Data too long for column 'mobile'", callable_obj=userprofile_create, 
								user=user_no_profile,
								mobile=u"这是个十个字的字符串这是个十个字的字符串这") # 21


		def test_property_fulladdress(self):
			user_no_profile = User.objects.get(username__exact='ihavenoprofile')

			# successful creation of non-foreign user profile
			address_1 = u"延长中路"
			address_2 = u"629弄"
			zip_code = 200072
			mobile = 13601894088
			province = 'shanghai'
			country = u'中国'
			in_foreign = False
			UserProfile.objects.create(user=user_no_profile, 
													address_1=address_1,
													address_2=address_2,
													zip_code=zip_code,
													mobile=mobile,
													province=province,
													country=country,
													in_foreign=in_foreign)

			user_profile = UserProfile.objects.get(user=user_no_profile)

			self.assertEqual(user_profile.user_id, user_no_profile.id)
			self.assertEqual(user_profile.address_1, address_1)
			self.assertEqual(user_profile.address_2, address_2)
			self.assertEqual(user_profile.zip_code, zip_code)
			self.assertEqual(user_profile.mobile, mobile)
			self.assertEqual(user_profile.province, province)
			self.assertEqual(user_profile.country, country)
			self.assertEqual(user_profile.in_foreign, in_foreign)

			expect_fulladdress = u"%s %s,%s,%s,%s" % (address_1, address_2, province, country, zip_code)

			self.assertEqual(user_profile.fulladdress, expect_fulladdress)

			# 若address_2 为  None
			user_profile.address_2 = None
			user_profile.save()

			expect_fulladdress = u"%s %s,%s,%s,%s" % (address_1, None, province, country, zip_code)

			self.assertEqual(user_profile.fulladdress, expect_fulladdress)



		def test_property_full_name(self):
			"""
			测试 @property fullname
			"""
			user_no_profile = User.objects.get(username__exact='ihavenoprofile')
			first_name = u"小红"
			last_name = u"欧阳"
			user_no_profile.first_name = u"小红"
			user_no_profile.last_name = u"欧阳"			


			# successful creation of non-foreign user profile
			address_1 = u"延长中路"
			address_2 = u"629弄"
			zip_code = 200072
			mobile = 13601894088
			province = 'shanghai'
			country = u'中国'
			in_foreign = False
			UserProfile.objects.create(user=user_no_profile, 
													address_1=address_1,
													address_2=address_2,
													zip_code=zip_code,
													mobile=mobile,
													province=province,
													country=country,
													in_foreign=in_foreign)

			user_profile = UserProfile.objects.get(user=user_no_profile)

			expect_fullname = u"%s%s" % (last_name, first_name)

			self.assertEqual(user_profile.fullname, expect_fullname)



class TestMembership(TestCase):

	def setUp(self):
		# setup user
		user = User.objects.create_user(username='ihavenomembership', 
								password='ihavenomembership', 
								email='zhang368@illinois.edu')
		user.is_active = True
		user.is_superuser = False
		user.is_staff = False

		user.save()

		self.assertEqual(user.username, 'ihavenomembership')
		self.assertEqual(user.email, 'zhang368@illinois.edu')
		self.assertEqual(user.is_active, True)
		self.assertEqual(user.is_superuser, False)
		self.assertEqual(user.is_staff, False)

		# setup group
		# done in fixure




	def test_membership_create(self):
		"""
		测试创建membership
		"""
		premium_group = UserGroup.objects.get(name__exact='premiumusergroup')
		enterprise_group = UserGroup.objects.get(name__exact='enterpriseusergroup')
		user_no_membership = User.objects.get(username__exact='ihavenomembership')
		date_joined = djtimezone.now()
		expire_date = date_joined + datetime.timedelta(days=30)

		# successful create
		membership = Membership.objects.create(user=user_no_membership,
												group=enterprise_group,
												date_joined=date_joined,
												expire_date=expire_date)
		membership = Membership.objects.get(user_id=user_no_membership.id)
		self.assertEqual(membership.user_id, user_no_membership.id)
		self.assertEqual(membership.group_id, enterprise_group.id)
		#self.assertEqual(membership.date_joined, djtimezone.now().date())
		#self.assertEqual(membership.expire_date, (djtimezone.now()+datetime.timedelta(30)).date())

		# 单用户多membership禁止
		membership_create = Membership.objects.create
		self.assertRaisesMessage(IntegrityError, "Duplicate entry", membership_create, 
				user=user_no_membership,
				group=premium_group,
				date_joined=date_joined,
				expire_date=expire_date)
		self.assertRaisesMessage(IntegrityError, "Duplicate entry", membership_create, 
				user=user_no_membership,
				group=enterprise_group,
				date_joined=date_joined,
				expire_date=expire_date)

		# missing date_joined
		self.assertRaisesMessage(IntegrityError, "Column 'date_joined' cannot be null", membership_create, 
				user=user_no_membership,
				group=enterprise_group,
				expire_date=expire_date)	

		# missing expire_date
		self.assertRaisesMessage(IntegrityError, "Column 'expire_date' cannot be null", membership_create, 
				user=user_no_membership,
				group=enterprise_group,
				date_joined=date_joined)



	def test__create_membership(self):
		premium_group = UserGroup.objects.get(name__exact='premiumusergroup')
		enterprise_group = UserGroup.objects.get(name__exact='enterpriseusergroup')
		user_no_membership = User.objects.get(username__exact='ihavenomembership')
		period = 1

		# successful create
		membership = Membership.objects._create_membership(user=user_no_membership,
												group=enterprise_group,
												period=period)	
		self.failUnless(membership)
		self.assertEqual(membership.user_id, user_no_membership.id)
		self.assertEqual(membership.group_id, enterprise_group.id)
		self.assertEqual((membership.expire_date - membership.date_joined).days, period*30)

		membership.delete()



		# invalid period should result in None creation
		# ---- period less than 1
		periods = [-1, 0, 0.1]
		for period in periods:
			membership = Membership.objects._create_membership(user=user_no_membership,
												group=enterprise_group,
												period=period)	
			self.failIf(membership)	



		# ---- period that is not integer, but is still valid
		periods = [1.1, 2.5, 3.7, 4.1]
		for period in periods:
			membership = Membership.objects._create_membership(user=user_no_membership,
												group=enterprise_group,
												period=period)	
			self.failUnless(membership)
			self.assertEqual((membership.expire_date - membership.date_joined).days, int(period)*30)	
			membership.delete()




	def test_upgrade_user(self):
		"""
		测试升级用户
		"""
		premium_group = UserGroup.objects.get(name__exact='premiumusergroup')
		enterprise_group = UserGroup.objects.get(name__exact='enterpriseusergroup')
		user_no_membership = User.objects.get(username__exact='ihavenomembership')
		period = 1

		# successful upgrade to premium
		status, msg = Membership.objects.upgrade_user(user=user_no_membership, group=premium_group, 
														period=period)
		self.failUnless(status)
		self.assertEqual(msg, u"用户升级成功")

		# fail upgrade to premium user
		status, msg = Membership.objects.upgrade_user(user=user_no_membership, group=premium_group, 
														period=period)
		self.failIf(status)
		self.assertEqual(msg, u"用户已经是高级用户，无法升级")

		status, msg = Membership.objects.upgrade_user(user=user_no_membership, group=enterprise_group, 
														period=period)
		self.failIf(status)
		self.assertEqual(msg, u"用户已经是高级用户，无法升级")

		membership = Membership.objects.get(user=user_no_membership)
		membership.delete()

		# successful upgrade to enterprise
		status, msg = Membership.objects.upgrade_user(user=user_no_membership, group=enterprise_group, 
														period=period)
		self.failUnless(status)
		self.assertEqual(msg, u"用户升级成功")

		# fail to upgrade to enterprise user
		status, msg = Membership.objects.upgrade_user(user=user_no_membership, group=premium_group, 
														period=period)
		self.failIf(status)
		self.assertEqual(msg, u"用户已经是企业用户，无法升级")

		status, msg = Membership.objects.upgrade_user(user=user_no_membership, group=enterprise_group, 
														period=period)
		self.failIf(status)
		self.assertEqual(msg, u"用户已经是企业用户，无法升级")

		membership = Membership.objects.get(user=user_no_membership)
		membership.delete()		




	def test_downgrade_user(self):
		pass

	def test_is_premium(self):
		premium_group = UserGroup.objects.get(name__exact='premiumusergroup')
		enterprise_group = UserGroup.objects.get(name__exact='enterpriseusergroup')
		user_no_membership = User.objects.get(username__exact='ihavenomembership')
		period = 1

		# successful upgrade to premium
		status, msg = Membership.objects.upgrade_user(user=user_no_membership, group=premium_group, 
														period=period)
		self.failUnless(status)
		self.assertEqual(msg, u"用户升级成功")

		self.assertEqual(Membership.objects.is_premium(user_no_membership), True)
		self.assertEqual(Membership.objects.is_enterprise(user_no_membership), False)

	def test_is_enterprise(self):
		premium_group = UserGroup.objects.get(name__exact='premiumusergroup')
		enterprise_group = UserGroup.objects.get(name__exact='enterpriseusergroup')
		user_no_membership = User.objects.get(username__exact='ihavenomembership')
		period = 1

		# successful upgrade to premium
		status, msg = Membership.objects.upgrade_user(user=user_no_membership, group=enterprise_group, 
														period=period)
		self.failUnless(status)
		self.assertEqual(msg, u"用户升级成功")

		self.assertEqual(Membership.objects.is_premium(user_no_membership), False)
		self.assertEqual(Membership.objects.is_enterprise(user_no_membership), True)
		

	def test_auto_renew(self):
		pass










		
