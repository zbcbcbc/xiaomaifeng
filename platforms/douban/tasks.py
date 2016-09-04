# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


import hashlib, logging

from django.core.cache import cache

from celery.utils.log import get_task_logger
from celery.exceptions import SoftTimeLimitExceeded
from celery.schedules import crontab
from celery.task import periodic_task



from platforms.tasks import PollCommentsBaseTask
from models import DoubanPost


# Logging
logger = get_task_logger('xiaomaifeng.platforms')


LOCK_EXPIRE = 30 # lock expires in 30 s, only in test phase


@periodic_task(base=PollCommentsBaseTask, task_name='platforms.douban.tasks.DoubanPollCommentsTask', run_every = crontab(hour="*", minute="*", day_of_week="*"), max_retries=1)
def douban_poll_comment():

		#TODO: post softtime limit
		poll_comments_digest = hashlib.md5('douban.poll_comments_task_periodic').hexdigest()
		lock_id = '%s-lock-%s' % ('douban.poll_comments_task_periodic', poll_comments_digest)

		# cache.add fails if if the key already exists
		acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
		# memcache delete is very slow, but we have to use it to take
		# advantage of using add() for atomic locking
		release_lock = lambda: cache.delete(lock_id)

		#用Lock防止重复Task发生
		if acquire_lock():

			DoubanPost.objects.poll_comments_fire_order(since_id_storage=douban_poll_comment.redis)







