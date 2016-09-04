# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import uuid

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils import timezone as djtimezone
from django.core.files.storage import default_storage

from siteutils.signalutils import receiver_subclasses
from dashboard.listing.models import *


if hasattr(settings, "AWS_SECRET_ACCESS_KEY"):
	try:
		from backends.S3Storage import S3Storage
		storage = S3Storage()
	except ImportError:
		raise S3BackendNotFound
else:
	storage = default_storage


def get_socialplatform_image_path(instance, filename):
	#filename = os.path.basename(filename)
	ext = filename.split('.')[-1].lower()
	filename = "%s.%s" % (uuid.uuid4(), ext)
	return os.path.join('img/social_platform', str(instance.name), filename)



class SocialPlatform(models.Model):

	name = models.CharField(max_length=10, unique=True, null=False, blank=False, editable=True)
	verbose_name = models.CharField(max_length=255, null=True, blank=True, editable=True)
	image_tiny = models.ImageField(upload_to=get_socialplatform_image_path, 
									storage=storage,
									null=True, blank=True, editable=True)


	def __unicode__(self):
		return u'%s' % self.name

	def __repr__(self):
		return u"%s:%s" % (self, self.pk)



class ClientBaseManager(models.Manager):

	def get_unique_or_none(self, **kwargs):
		try:
			return self.get(**kwargs)
		except:
			return None

	def get_authorize_url(self, redirect_uri=None, mac=False, **kwargs):
		"""
		"""
		raise NotImplementedError



class ClientBase(models.Model):
	"""
	Base class for client
	"""

	user = models.OneToOneField(settings.AUTH_USER_MODEL, null=False, editable=False, related_name="%(class)s")
	
	# 社交用户数据
	username = models.CharField(max_length=255, null=True, editable=True)
	password = models.CharField(max_length=255, null=True, editable=True)
	uid = models.BigIntegerField(unique=True, null=False, editable=False)
	add_date = models.DateTimeField(null=False, editable=True) # 网站时间
	user_name = models.CharField(max_length=255, null=False, editable=True)

	# 社交用户连接数据
	access_token = models.CharField(max_length=255, null=False, editable=False) # 支持mac token 和 普通 access_token
	refresh_token = models.CharField(max_length=255, null=True, editable=False)
	expires_in = models.FloatField(default=0.0, null=False, editable=True)	


	class Meta:
		abstract = True	
		unique_together = (('user', 'uid'),)

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)


	def save(self, *args, **kwargs):
		if not self.id and not self.add_date:
			# always store UTC time in database
			self.add_date = djtimezone.now()

		super(ClientBase, self).save(*args, **kwargs)



	def get_absolute_url(self):
		"""
		"""
		raise NotImplementedError


	def _get_client_info(self, write_to_db=True, **kwargs):
		"""
		获取社交用户基本资料
		获取后强制创建用户,否则失败
		返回(状态，内容，信息)
		"""
		raise NotImplementedError


	def update_client_profile(self, write_to_db=True, **kwargs):
		"""
		更新社交帐户资料
		更新或者创建Client
		返回(状态，内容，信息)
		"""
		raise NotImplementedError


class SocialClientBase(ClientBase):
	"""
	Base Class for Social Client
	"""

	social_platform = models.ForeignKey(SocialPlatform, null=False, on_delete=models.CASCADE, editable=True)

	class Meta:
		abstract = True


	# 社交用户优先级
	PRIORITY_HIGH = 2
	PRIORITY_MEDIUM = 1
	PRIORITY_LOW = 0

	PRIORITY_CHOICES = (
		(PRIORITY_LOW, u'低刷新频率'),
		(PRIORITY_MEDIUM, u'中等刷新频率'),
		(PRIORITY_HIGH , u'高刷新频率')
		)

	priority = models.CharField(max_length=1, default=PRIORITY_MEDIUM, choices=PRIORITY_CHOICES, null=False, editable=True)



		

	def update_priority(self, write_to_db=True, **kwargs):
		"""
		用法：计算出社交状态的优先级
		0: 低优先级
		1: 中优先级
		2: 高优先级

		"""

		raise NotImplementedError


	def create_post(self, merchandise, message=None, write_to_db=True, **kwargs):   	
		"""
		创建社交Post
		返回tuple，(状态,内容，信息)
		强制创建
		注意：创建社交Post一定要在创建社交Post之前
		"""
		raise NotImplementedError

	def update_post(self, post, write_to_db=True, delete_on_notfound=True, **kwargs):
		"""
		更新社交Post信息，不包括评论
		强制更新
		返回(状态，内容，信息)
		"""
		raise NotImplementedError

	def get_post_comments(self, post, **kwargs):
		"""
		根据某条社交Post找到所有大于since_id的社交Post评论
		速度性大于稳定性
		返回(内容(List))
			内容：list形式的评论，如错误返回空list,即返回0条评论
				返回list 的 评论id 应该从小到大，但是不能保证

		"""
		raise NotImplementedError


class SocialPostBaseManager(models.Manager):

	def get_unique_or_none(self, **kwargs):
		try:
			return self.get(**kwargs)
		except:
			return None

	def filter_posts(self, **kwargs):
		return self.filter(**kwargs)


	def filter_posts_and_lock(self, **kwargs):
		"""
		获取post的同时lock保持row的atomic property
		"""
		return self.select_for_update().filter(**kwargs)


	def poll_comments_fire_order(self, priority=1, since_id_storage=None):
		"""
		抓去评论并且建立交易
		"""
		raise NotImplementedError


class SocialPostBase(models.Model):
	"""
	Base class for Social post base
	"""

	# Post信息
	pid = models.CharField(max_length=255, null=False, unique=True, editable=False)
	uid = models.BigIntegerField(null=False, editable=False)
	post_date = models.DateTimeField(auto_now_add=True, null=False, editable=True)
	text = models.CharField(max_length=255, null=True, editable=True)

	# 商品信息
	limit = models.Q(app_label = 'listing', model = 'PhysicalItem') | \
			models.Q(app_label = 'listing', model = 'DigitalItem') | \
			models.Q(app_label = 'listing', model = 'PaybackFund') | \
			models.Q(app_label = 'listing', model = 'DonationFund') | \
			models.Q(app_label = 'listing', model = 'EventItem')

	merchandise_type = models.ForeignKey(ContentType, limit_choices_to=limit, null=False, on_delete=models.CASCADE)
	merchandise_id = models.PositiveIntegerField()
	merchandise_object = generic.GenericForeignKey('merchandise_type', 'merchandise_id')

	# post 筛选信息
	since_id = models.BigIntegerField(default=0, null=False, editable=True)
	comment_count = models.PositiveIntegerField(default=0, null=False, editable=False)

	# priority 信息
	priority = models.CharField(max_length=1, null=False, default=SocialClientBase.PRIORITY_MEDIUM, 
								choices=SocialClientBase.PRIORITY_CHOICES, editable=True)

	# 各个社交网络的独立信息在Subclass中

	class Meta:
		abstract = True

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)



@receiver_subclasses(models.signals.pre_delete, SocialPostBase, 'platforms.signals.pre_delete_clear_since_id', weak=False)
def clear_since_id_record(sender, instance, **kwargs):
	"""
	清除since_id_storage的since_id record
	"""

	logger.info(u"deleting %s since_id ..." % instance)

	redis_conn = redis.Redis("localhost") #WARNING: use redis conn from settings or other cache method
	redis_conn.delete(instance.id) #WARNING: catch key error here




