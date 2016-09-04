# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from celery.task import PeriodicTask
import redis


class PollCommentsBaseTask(PeriodicTask):
	"""
	抓去评论Base Task Class
	连接redis,保存post since_id
	"""

	ignore_result = True
	abstract = True
	_redis = None
	send_error_emails = True


	@property
	def redis(self):
		if self._redis is None:
			self._redis = redis.Redis("localhost")
		return self._redis


