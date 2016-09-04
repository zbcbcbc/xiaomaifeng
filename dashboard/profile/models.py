# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng



__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


"""
WARNING: Never cache at model level
"""

import datetime, logging

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage
from django.utils import timezone as djtimezone
from django.dispatch import receiver

from modelfields import CountryField, CityField
from payment.alipay.modelfields import *
from localflavor_cn.provinces import CN_PROVINCE_CHOICES
from accounts.signals import user_activated as user_activated_signal
from accounts.backends.default.views import ActivationView


logger = logging.getLogger('xiaomaifeng.profile')




class UserProfile(models.Model):
	"""
	用户联系方式参数, 仅支持中国大陆用户，非中国大陆用户无法进行购买实体物品交易
	"""
	user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, null=False, blank=False, editable=False)
	address_1 = models.CharField(max_length=128, null=True, blank=False, editable=True)
	address_2 = models.CharField(max_length=64, null=True, blank=True, editable=True)
	province = models.CharField(max_length=100, choices=CN_PROVINCE_CHOICES, null=True, blank=False, editable=True)
	country = CountryField(null=True, blank=False, editable=True)
	zip_code = AlipayReceiverZipField(null=True, blank=False, editable=True)
	mobile = AlipayReceiverMobileField(null=True, blank=False, editable=True)
	in_foreign = models.BooleanField(default=False, blank=True, editable=True)


	def __unicode__(self):
		return u"user(%s)'s profile" % (self.pk)

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)


	def get_absolute_url(self):
		return reverse("dashboard:profile:userprofile-detail")

	@property
	def fullname(self):
		#WARNING: one extra db hit
		return u"%s%s" % (self.user.last_name, self.user.first_name)

	@property
	def fulladdress(self):
		return u"%s %s,%s,%s,%s" % (self.address_1, 
									self.address_2 or None, 
									self.get_province_display(), 
									self.get_country_display(),
									self.zip_code)



@receiver(models.signals.post_save, sender=User, weak=False, dispatch_uid="signals.user_activated.create_user_profile")
def create_user_profile(sender, instance, created, **kwargs):
	if created and not UserProfile.objects.filter(user=instance).exists():
		try:
			UserProfile.objects.create(user=instance)
		except Exception, err:
			logger.critical(u"create %r's userprofile fail... reason:%s", (user, err))



class UserHealthProfileManager(models.Manager):

	def refresh_all_user_health(self):
		user_health_profiles = self.all()
		for user_health_profile in user_health_profiles:
			user_health_profile.calculate_health()

	def find_abnormal_users(self):
		"""
		WARNING: two db hits
		Return a query set
		"""
		return []


class UserHealthProfile(models.Model):
	"""
	用户帐户健康程度参数
	"""

	HEALTHY = '3'
	WATCHING = '2'
	ABNORMAL = '1'

	HEALTH_LEVEL_CHOICES = (
		(HEALTHY, u"健康"),
		(WATCHING, u"观察中"),
		(ABNORMAL, u"反常")
	)

	user = models.OneToOneField(User, primary_key=True, null=False, blank=False, editable=False)
	health_level = models.CharField(max_length=1, null=False, default=HEALTHY, choices=HEALTH_LEVEL_CHOICES, editable=True)

	objects = UserHealthProfileManager()

	def __unicode__(self):
		return u"user(%s)'s health: %s" % (self.pk, self.health_level)

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)


	def calculate_health(self):
		"""
		决定用户的health level，
		"""
		#STUB
		return '1'


@receiver(models.signals.post_save, sender=User, weak=False, dispatch_uid="create_user_health_profile")
def create_user_health_profile(sender, instance, created, **kwargs):
	if created and not UserHealthProfile.objects.filter(user=instance).exists():
		try:
			UserHealthProfile.objects.create(user=instance)
		except Exception, err:
			logger.critical(u"create %r's user health profile fail... reason:%s", (user, err))



class UserGroup(models.Model):
	name = models.CharField(max_length=100, null=False, unique=True, editable=True)
	display_name = models.CharField(max_length=100, null=True, editable=True)
	members = models.ManyToManyField(User, null=True, blank=True, through="Membership", editable=True)

	def __unicode__(self):
		return u"%s" % self.display_name or self.name

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)





class MembershipManager(models.Manager):


	def _create_membership(self, user, group, period=1):
		"""
		wrapper around membership creation
		default period is in # 30 days
		"""
		try:
			if period < 1:
				raise Exception(u"周期不能小于1")

			date_joined = djtimezone.now()
			expire_date = date_joined + datetime.timedelta(days=30*int(period))

			membership = self.create(user=user, group=group, date_joined=date_joined, expire_date=expire_date)
			return membership
		except Exception, err:
			logger.error(u"%s创建Membership失败, 原因:%s" % (user, err))
			return None


	def upgrade_user(self, user, group, period=1):
		"""
		尝试添加用户到高级用户，在此省略收费步骤仅仅用于测试
		如果用户已经是高级或者企业用户，则默认为失败
		"""
	
		logger.info(u"用户%s尝试升级用户" % (user))

		if self.is_premium(user):
			logger.warning(u"%s已经是高级用户，无法升级" % (user))
			return (False, u"用户已经是高级用户，无法升级")
			
		elif self.is_enterprise(user):
			logger.warning(u"%s已经是企业用户，无法升级" % (user))
			return (False, u"用户已经是企业用户，无法升级")
		else:
			# 尝试添加用户到指定用户群
			
			membership = self._create_membership(user=user, group=group, period=period)
			if membership:
				return (True, u"用户升级成功")
			else:
				return (False, u'用户升级失败,请联系客服')


	def downgrade_user(self, user):
		logger.info(u"用户%r尝试降级用户" % (user))

		try:
			#TODO: what if user has no membership?
			user.membership.delete()
			return (True, u"降级用户成功")
		except Exception, err:
			logger.error(u"用户%s降级失败,原因:%s" % (user, err))
			return (False, u"降级用户失败")


	def is_premium(self, user):
		"""
		监测用户是否是高级用户
		只有在is active 用户下才有效
		"""	
		try:
			premium_group = UserGroup.objects.get(name__exact='premiumusergroup')
			self.get(user=user, group=premium_group)
			return True
		except self.model.DoesNotExist:
			# Throw DoesNotExist Error, 说明没有此用户纪录
			#logger.info(u"%s:%s" % ("is_premium", u"没有%s纪录" % user))
			return False
		except Exception, err:
			logger.critical("%r is_premium check err: %s" % (user, err))


	def is_enterprise(self, user):
		"""
		监测用户是否是企业用户
		TOTO: catch does not exist exception
		"""
		try:
			enterprise_group = UserGroup.objects.get(name__exact='enterpriseusergroup')
			self.get(user=user, group=enterprise_group)
			return True
		except self.model.DoesNotExist:
			# Throw DoesNotExist Error, 说明没有此用户纪录
			#logger.info(u"%s:%s" % ("is_enterprise", u"没有%s纪录" % user))
			return False
		except Exception, err:
			logger.critical("%r is_enterprise check err: %s" % (user, err))




	def user_extend_membership(self, user, days):
		"""
		延长用户membership by # days
		"""
		pass


	def user_quit_membership(self):
		pass


	def handle_expired_membership(self):
		"""
		删除或者更新已经过期用户Membership
		"""
		logger.warning(u"删除或者自动更新过期Membership")
		memberships = self.all()
		for membership in memberships:
			if membership.is_expires:
				# 会员过期
				if membership.auto_renew:
					# TODO:自动更新会员
					# STUB
					pass
				else:
					# 删除会员纪录
					membership.delete()






class Membership(models.Model):
	"""
	一个用户只能拥有一个membership
	"""
	user = models.OneToOneField(User, null=False, editable=False)
	group = models.ForeignKey(UserGroup, null=False, editable=True)
	date_joined = models.DateField(null=False, editable=True)
	expire_date = models.DateField(null=False, editable=True)
	auto_renew = models.BooleanField(default=False, null=False, editable=True)
	"""
	自定义的MembershipManager
	"""
	objects = MembershipManager()

	def __unicode__(self):
		return u"user(%s)'s membership" % (self.id)

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)


	@property
	def is_expires(self):
		OFFSET = 60 # in seconds
		return djtimezone.now() > self.expire_date


	class Meta:
		"""
		一个用户只能在一个小组内出现一次
		"""
		unique_together = (('user', 'group'),)








