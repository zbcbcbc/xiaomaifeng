# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang, Jian Chen"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


import time, datetime, logging

from django.utils import timezone as djtimezone
from django.db import models, IntegrityError
from django.db.models.signals import post_save
from django.core.urlresolvers import reverse


from dashboard.listing.models import Item, Fund
from dashboard.orders.tasks import create_order_task
from platforms.models import *
from signals import *
from signal_handlers import *
from douban_python import *
from modelfields import *
from siteutils.comment import action_from_comment # reimport from xiaomaifeng_util



logger = logging.getLogger('xiaomaifeng.platforms')



class DoubanClientManager(ClientBaseManager):

	
	def get_unique_or_none(self, **kwargs):
		try:
			return self.get(**kwargs)
		except:
			return None


	def get_authorize_url(self, redirect_uri=None, mac=False, **kwargs):
		'''
		return the authorization url that the user should be redirected to.
		返回(内容)
			内容：authorize_url
		'''
		TAG = 'douban get authorize url'

		logger.info(u"%s:%s" % (TAG, u"豆瓣获取Authorize_url..."))

		url = douban_get_authorize_url(**kwargs)
		return url


	def create_authorized_doubanclient(self, user, code, create_on_success=True, **kwargs):
		'''
		如果成功返回结果，如果不成功，返回None
		不返回错误信息
		return access token as a JsonDict: {"access_token":"your-access-token","expires_in":12345678,"uid":1234}, expires_in is represented using standard unix-epoch-time
		'''
		TAG = u'douban request access token and create'

		SUCCESS_MSG = u'用户连接豆瓣成功'
		ERROR_MSG = u'用户连接豆瓣失败，请稍后尝试或者联系客服'

		logger.info(u"%s:%s" % (TAG, u"%r尝试获取豆瓣Access Token..." % user))

		try:
			r = douban_request_access_token(code, **kwargs)
		except DoubanAPIError, err:
			logger.error(u"%s:%s" % (TAG, u"%r尝试获取豆瓣Access Token失败，原因:%s" % (user, err)))
			return (False, None, ERROR_MSG)           
		else:
			# 返回成功
			try:
				access_token = r['access_token']
				expires_in = r['expires_in']
				uid = r['douban_user_id']
				refresh_token = r['refresh_token']

				if create_on_success:
					client = DoubanClient(user=user,
								access_token=access_token,
								uid=uid,
								social_platform=SocialPlatform.objects.get(name__exact='douban'),
								add_date=djtimezone.now(),
								expires_in=expires_in,
								refresh_token = refresh_token)
					status = client._get_client_info(write_to_db=False)
					if status:
						client.save(force_insert=True)
						return (True, client, SUCCESS_MSG)
					else:
						return (False, None, ERROR_MSG)
				else:
					return (True, r, None)

			except Exception, err:
				logger.critical(u"%s:%s" % (TAG, u"%r尝试获取豆瓣access token失败，原因:%s" % (user,err)))
				return (Fasle, None, ERROR_MSG)



# Check if auth has expired decorator
def douban_auth2_required(func):

	def _douban_auth2_required(self, *args, **kwargs):    
		if self.is_expires:
			logger.warning(u'%r授权过期' % self)
			return func(self, *args, **kwargs)
	return _douban_auth2_required




class DoubanClient(SocialClientBase):
	'''
	API client using synchronized invocation.
	'''
	
	# 豆瓣用户‘说’miniblog独有社交数据 ?? develop algorithm to find friends_count用相互关注(可以用followers, following返回的两个列表对比找出相互关注)还是好友
	followers_count = models.PositiveIntegerField(default=0, null=False, editable=False)
	following_count = models.PositiveIntegerField(default=0, null=False, editable=False)
	
	objects = DoubanClientManager()


	def __unicode__(self):
		return u"豆瓣帐户(%s):%s" % (self.id, self.user_name)


	def save(self, *args, **kwargs):
		super(SocialClientBase, self).save(*args, **kwargs)


	def get_absolute_url(self):
		return reverse('platforms:douban:client-detail', args=[str(self.id)])



	def _doubanAPI(self, path, method, **kwargs):
		"""
		如果出错, 抛出DoubanAPIError
		Subject to douban api change
		path should be change for different usages
		"""
		# !!! add expire token checking here ???
		return douban_execute_api(self.access_token, path, method, **kwargs)




	def _refresh_token(self):
		try:
			logger.info(u"refreshing token >>>")
			r = douban_refresh_token(self.refresh_token)
		except DoubanAPIError, err:
			print 'douban refresh token err:', err
		else:
			# save the new access_token and refresh_token to database; error handle
			logger.info(u"saving new token to db >>>")
			self.access_token = r['access_token']
			self.refresh_token = r['refresh_token']
			self.expires_in = r['expires_in']
			self.add_date = djtimezone.now()
			logger.info(u"save new token success %s, %s" %(r['access_token'], r['refresh_token']))
			self.save()



	@property
	def is_expires(self):
		"""
		查看豆瓣用户授权是否过期
		如果数据没有保存到数据库，返回没有过期
		返回True/False
		"""
		TAG = u'douban is expires'
		#logger.info(u"%s:%s" % (TAG, u"%s检查豆瓣授权是否过期..." % self))

		EXPIRE_OFFSET = 60 # in seconds

		time_diff = (djtimezone.now() - self.add_date).total_seconds()
		self.expires_in -= time_diff
		r = not self.access_token or self.expires_in <= EXPIRE_OFFSET
		return r


	def _get_client_info(self, write_to_db=True, **kwargs):
		"""
		获取豆瓣用户基本资料
		返回(状态)
		"""
		TAG = 'douban update client profile'

		logger.info(u"%s:%s" % (TAG, u'更新%r 资料中...' % self))

		try:
			path = 'shuo/v2/users/@me'
			method = 'GET'
			r = self._doubanAPI(path, method, uid=self.uid)
		except DoubanAPIError, err:
			# first: check token expire 106, then call function self again
			if err.error_code == 106:
				logger.critical(u'code 106, token expires, calling refresh...')
				self._refresh_token()
				self._get_client_info(write_to_db=write_to_db, **kwargs)
			elif err.error_code == 'Douban urllib2 URLError':
				logger.critical(u'Douban urllib2 URLError')
				return False
			else:
				logger.error(u"%s:%s" % (TAG, u"更新%r 资料失败, 原因:%s" % (self, err)))
				return False
		else:
			try:
				self.user_name = r['screen_name']
				self.following_count = r['following_count']
				self.followers_count = r['followers_count']

				if write_to_db: self.save()

				return True
			except Exception, err:
				logger.critical(u"%s:%s" % (TAG, u"%r获取基本资料失败, 原因:%s" % (self, err)))
				return False   

  



	#@douban_auth2_required
	def update_client_profile(self, write_to_db=True, **kwargs):
		"""
		更新豆瓣用户资料
		返回(状态，内容，信息)
		"""
		TAG = 'douban update client profile'
		logger.info(u"%s:%s" % (TAG, u'更新%r 资料中...' % self))

		try:
			path = 'shuo/v2/users/@me'
			method = 'GET'
			r = self._doubanAPI(path, method, uid=self.uid)
		except DoubanAPIError, err:
			# second: check token expire 106, then call function self again
			if err.error_code == 106:
				logger.critical(u'code 106, token expires, calling refresh...')
				self._refresh_token()
				self.update_client_profile(write_to_db=write_to_db, **kwargs)
			elif err.error_code == 'Douban urllib2 URLError':
				logger.critical(u'Douban urllib2 URLError')
				return (False, None, None)
			else:
				logger.error(u"%s:%s" % (TAG, u"更新%r 资料失败, 原因:%s" % (self, err)))
				return (False, None, None)
		else:
			following_count = r.get('following_count', None)
			followers_count = r.get('followers_count', None)

			if following_count: self.following_count = following_count
			if followers_count: self.followers_count = followers_count
			#WARNING 强制更新
			if following_count and followers_count and write_to_db:
				try:
					self.save(force_update=True) 
					return (True, None, u'豆瓣用户资料更新成功')
				except Exception, err:
					logger.critical(u"%s:%s" % (TAG, u"%r更新详细资料失败, 原因:%s" % (self, err)))
					return (False, None, u'豆瓣用户更新资料失败')



	#@douban_auth2_required
	def create_post(self, merchandise, message=None, write_to_db=True, **kwargs):
		"""
		创建有照片或者无照片广播，若物品有照片则默认有照片广播
		返回tuple，(状态,内容，信息)
		注意：创建豆瓣一定要在创建豆瓣数据之前
		错误：如果创建豆瓣后豆瓣数据创建失败，则会使豆瓣无效
		Database Transaction
		"""
		
		from dashboard.listing.models import Item, Fund

		TAG = 'douban create miniblog'

		SUCCESS_MSG = u'用户发布到豆瓣广播成功' #TODO
		ERROR_MSG = u'用户发布到豆瓣广播失败'

		logger.info(u"%s:%s" % (TAG, u'%r 发布豆瓣广播中...' % self))

		if isinstance(merchandise, Item):
			status = message or merchandise.description
			status += u' #小麥蜂 #出售'
		elif isinstance(merchandise, Fund):
			status = message or merchandise.description
			status += u' #小麥蜂 #集资'
		else:
			logger.critical(u"%s:%s" % (TAG, u"%r 发布物品:%r 无法识别" % (self, merchandise)))
			return (False, None, ERROR_MSG)
		try:
			image = open(merchandise.image.path, 'rb')
		except:
			image = None
		try:
			if image:
				path = 'shuo/v2/statuses/'
				method = 'POST'
				r = self._doubanAPI(path, method, text=status, image=image)
			else:
				path = 'shuo/v2/statuses/'
				method = 'POST'
				# this content doesn't involve image
				r = self._doubanAPI(path, method, text=status) # throw DoubanAPIError
		except DoubanAPIError, err:
			# third: check token expire, recall function itself
			if err.error_code==106:
				logger.critical(u'code 106, douban token expires, calling refresh...')
				self._refresh_token()
				self.create_post(merchandise, message=message, write_to_db=write_to_db, **kwargs)
			elif err.error_code == 'Douban urllib2 URLError':
				logger.critical(u'Douban urllib2 URLError')
				return (False, None, ERROR_MSG)
			elif err.error_code == 103:
				# invalid refresh token
				logger.info(u'douban token %s, douban refresh_token %s' % (self.access_token, self.refresh_token))
				self.delete()
				logger.info(u'delete client')
				return (False, None, ERROR_MSG)
				#self.create_post(content, message=message, write_to_db=write_to_db, **kwargs)
				# 账号、IP或应用非法，暂时无法完成此操作
				# 可以重新尝试
				# 提交相同信息
			else:
				logger.error(u"%s:%s" % (TAG, u"%r 发布广播失败，原因:%s" % (self, err)))
				return (False, None, ERROR_MSG)
		else:
			"""
			注意，Tightly coupled DoubanPost creation
			"""
			try:
				uid = r['user']['id']
				if str(uid) != str(self.uid):
					raise Exception(u"创建的豆瓣用户%s和用户%s不符合" % (uid, self.uid))

				post = DoubanPost(merchandise_object=merchandise,
								client_id=self.id, 
								pid=r['id'], 
								uid=uid,
								comment_count=r['comments_count'], 
								reshared_count=r['reshared_count'],
                                #reposts_count changed to reshared_count
								text=status,
								priority=self.priority)
				if write_to_db: post.save(force_insert=True) # 强制创建
				
				return (True, post, SUCCESS_MSG)

			except Exception, err:
				logger.critical(u"%s:%s" % (TAG, u"%r 创建DoubanPost失败，原因:%s" % (self, err)))
				return (False, None, ERROR_MSG)



	#@douban_auth2_required
	def update_post(self, post, write_to_db=True, delete_on_notfound=True, **kwargs):
		"""
		更新豆瓣广播信息，不包括评论
		如果没有在豆瓣广播上找到此条广播，选择默认永久删除此广播，不再刷新此广播状态
		返回(状态(Boolean)，内容(DoubanPost)，信息(String))
		"""
		TAG = 'douban update post'

		SUCCESS_MSG = u'豆瓣更新成功'
		ERROR_MSG = u'豆瓣更新失败'

		logger.info(u"%s:%s" % (TAG, u'%r更新%r 中...是否写入数据库:%s, 没有找到是否删除:%s' % \
										(self, post, write_to_db, delete_on_notfound)))

		try:
			path = 'shuo/v2/statuses/' + str(post.pid)
			method = 'GET'
            # post.id is hard coded in url
			r = self._doubanAPI(path, method)
		except DoubanAPIError, err:
			# fourth: check token expire 106, then call function self again
			if err.error_code == 106:
				logger.critical(u'code 106, token expires, calling refresh...')
				self._refresh_token()
				self.update_post(post, write_to_db = write_to_db, delete_on_notfound = delete_on_notfound, **kwargs)
			elif err.error_code == 'Douban urllib2 URLError':
				logger.critical(u'Douban urllib2 URLError')
				return (False, None, ERROR_MSG)
			else: #?? what is the code for not found
				# post not found on douban! 
				logger.warning(u"%s:%s" % (TAG, u"%r 更新%r 不存在" % (self, post)))

				if delete_on_notfound: post.delete() #WARNING

				logger.error(u"%s:%s" % (TAG, u"%r 更新%r 失败，原因:%s" % (self, post, err)))
				return (False, None, ERROR_MSG)
		else:
			try:
				uid = r['user']['id']
				if str(uid) != str(self.uid):
					logger.critical(u"%s:%s" % (TAG, u"%r更新%r失败，原因:%s" % (self, post, u'id are different?!')))
					post.delete() #WARNING
					raise Exception(u'广播拥有者id和豆瓣用户id不符合')
				post.comment_count = r['comments_count']
				post.reshared_count = r['reshared_count']
				post.text = r['text']

				if write_to_db: post.save(force_update=True) #强制更新

				return (True, post, SUCCESS_MSG)
			except Exception, err:
				logger.critical(u"%s:%s" % (TAG, u"%r 读取%r 数据失败，原因:%s" % (self, post, err)))
				return (False, None, ERROR_MSG)


	#@douban_auth2_required
	def get_post_comments(self, post, **kwargs):
		"""
		根据某条豆瓣找到所有大于since_id的豆瓣评论  called start in douban
		速度性大于稳定性
		错误：未分别页面，在评论很多的情况可能出现评论未读取
			count 参数仍然没有得到官方文档的确认
			默认count = 20
		返回(内容(List))
			内容：list形式的评论，如错误返回空list,即返回0条评论
				返回list 的 评论id 应该从小到大，但是不能保证

		"""
		TAG = 'douban miniblog get post comments'
		logger.info(u"%s:%s" % (TAG, u"%r'getting comments of %r..." % (self, post)))
		
		if post.uid != self.uid:
			post.delete() #WARNING
			logger.critical(u"%s:%s" % (TAG, u"%r getting comment of %r failed，reason:%s" % (self, post, u'id are different?!')))
			return []

		# try to get start:since_id
		sid = kwargs.get('start',0)
		try:
			path = 'shuo/v2/statuses/'+ str(post.pid) + '/comments'
			method = 'GET'
			# don't need to pass in id= post.pid, it's hard encoded in path, don't need / at the end
			r = self._doubanAPI(path, method, start=sid)
			comments = r #.get('comments', None)
			comments = list(comments) if comments else []
			return comments
		except DoubanAPIError, err:
			# call refresh token
			logger.error(u"%s:%s" % (TAG, u"%r getting comment of %r failed，reason:%s" % (self, post, err)))
			return []



	# working on it CJ
	#@douban_auth2_required
	def revoke_oauth2(self, **kwargs):
		"""
		驳回用户授权，此方法非常暴力，慎用
		返回(状态，内容，信息)
		"""
		TAG = u'douban revoke oauth2 access token'
		logger.info(u"%s:%s" % (TAG, u'%r 驳回豆瓣授权中...' % (self)))

		try:
			r = douban_revoke_oauth2(self.access_token)
			if 'result' not in r or r.result != 'true':
				logger.warning(u"%s:%s" % (TAG, u"%r 驳回豆瓣授权失败，返回值:%s" % (self, r)))
				return (False, None, u'豆瓣请求返回错误')
			else:
				return (True, None, None)
		except DoubanAPIError, err:
			logger.error(u"%s:%s" % (TAG, u"%r 驳回豆瓣授权失败，原因:%s" % (self, err)))
			return (False, None, err)

# douban has no similar setting
'''
	@douban_auth2_required
	def end_session(self, **kwargs):
		"""
		结束用户session
		返回(状态，内容，信息)
		"""
		TAG = u'sinadouban end session'
		logger.info(u"%s:%s" % (TAG, u'%s 终止豆瓣Session中...' % (self)))

		try:
			path = 'account/end_session'
			method = 'GET'            
			r = self._doubanAPI(path, method, access_token=self.access_token)
			return (True, None, None)
		except DoubanAPIError, err:
			logger.error(u"%s:%s" % (TAG, u"%s 终止豆瓣Session失败，原因:%s" % (self, err)))
			return (False, None, err)
'''



class DoubanPostManager(SocialPostBaseManager):


	def poll_comments_fire_order(self, priority=1, since_id_storage=None):
		"""
		抓去豆瓣评论并且下单
		每页返回回复最大数不详
		返回回复以从旧到新！！排列
		start 参数为所有回复的由旧到新依次为0,1,2,3,4...而不是独有的comment_id
		"""
		logger.warning("Find all douban post and search for comemnts...")
		posts = self.all() #TODO suppose to filter by priority. Post is cached here
		for post in posts:
			post_storage_key = "douban%s" % post.id
			# 获取comments
			seller_doubanclient = post.client

			# 同时获取db 和 storage 储存的since_id, 比较出最大的避免重复filter comment
			cur_since_id_post = post.since_id
			cur_since_id_storage = since_id_storage.get(post_storage_key) or 0 if since_id_storage else 0 # 避免None
			cur_since_id = int(max(cur_since_id_post, cur_since_id_storage))

			comments=[]
			comments_temp = seller_doubanclient.get_post_comments(post, start=0)
			start = 0

			# if return is not []
			while comments_temp != []:
				# the iteration would go from old to new, small id to big id
				for k in comments_temp:
					if k['id'] > cur_since_id:
						comments.append(k)
						#print u"%s douban_new_comment" %k['text'] #debugging
					start = start +1
					#print u"%s" %k['text'] #debugging
				# if k reaches end, we call with the newest start, if no new returns, while ends; otherwise continue 
				comments_temp = seller_doubanclient.get_post_comments(post, start=start)

			
			for comment in comments:
				# 从comment中读取关键数据, 如果任意数据读取失败则忽视此评论
				comment_id = comment.get('id', None)
				text = comment.get('text', None)
				comment_user = comment.get('user', None)
				comment_user_id = comment_user.get('id', None) if comment_user else None
				if not comment_id or not text or not comment_user_id:
					logger.warning("%r douban reply key error" % post)
					pass

				elif comment_user_id == seller_doubanclient.user_id:
					logger.warning(u'seller and buyer are the same person, ignore')
					pass

				else:
					if comment_id <= cur_since_id:
						logger.warning("This comment(%s) is a repeat comment, ignore it" % comment_id)
						pass
					else:
						# 有效的comment_id, 从用户评论判定用户行为
						action, amount = action_from_comment(text)
						if action == 'buy':
							buyer_doubanclient = DoubanClient.objects.get_unique_or_none(uid=comment_user_id) #Cache payer_doubanclient here
							if buyer_doubanclient:

								buyer = buyer_doubanclient.user #WARNING
								seller = seller_doubanclient.user #WARNING
								social_platform = buyer_doubanclient.social_platform
								body = post.text
								merchandise = post.merchandise_object
								quantity = int(amount) if amount else 0

								create_order_task.apply_async(args=[buyer, seller, text, social_platform, body, merchandise, quantity])
								#endif
							else:
								# 用户没有在网站注册
								logger.warning("Comment user is not a website resigstered user")
								pass
						else:
							# 用户的行为为打酱油
							logger.warning("This user da jiang you, ignore")
							pass
						#endif 判定用户行为
						cur_since_id = max(comment_id, cur_since_id)
						since_id_storage.set(post_storage_key, cur_since_id)
						logger.warning("since_id_storage update since_id:%s " % cur_since_id)
					#endif 判定有效comment_id

			# Endfor 读取评论列表
			post.since_id = cur_since_id
			post.save(force_update=True)
			logger.warning("update since_id:%s" % post.since_id)
			logger.warning("%r update success" % post)
			#TODO: 危险，如果since_id没有save,则会导致重复下单
		


class DoubanPost(SocialPostBase):

	# 豆瓣帐户
	client = models.ForeignKey(DoubanClient, on_delete=models.CASCADE)
	# 豆瓣独有的相关信息
	reshared_count = models.PositiveIntegerField(default=0, null=False, editable=True)

	objects = DoubanPostManager()



	class Meta(SocialPostBase.Meta):
		unique_together = (('merchandise_id', 'client', 'merchandise_type'),)


	def __unicode__(self):
		return u"豆瓣Post(%s)" % (self.id)


	def save(self, *args, **kwargs):
		"""
		更新用户豆瓣广播的优先级, cache priority
		"""
		if not self.id:
			if str(self.uid) != str(self.client.uid):
				raise IntegrityError(u"豆瓣拥有者id和豆瓣用户id不符合")
		self.update_priority(write_to_db=False) #TODO: cache it
		super(DoubanPost, self).save(*args, **kwargs)


	def update_priority(self, write_to_db=True, **kwargs):
		"""
		用法：计算出豆瓣状态的优先级，优先级参数包括用户好友总数，跟随总数，豆瓣评论总数， 豆瓣转发总数
			0: 低优先级
			1: 中优先级
			2: 高优先级

		调和参数: FRIENDS_WATERMARK, VISITORS_WATERMARK, COMMENT_WATERMARK
			通过调整这3个参数，来调整人人状态优先级分布。

		"""
		TAG = 'douban get priority'

		FRIENDS_WATERMARK = 300
		FOLLOWERS_WATERMARK = 300
		COMMENTS_WATERMARK = 50

		logger.info(u"%s:%s" % (TAG, u'%s 更新优先级中...' % (self))) 

		friends_weight = 1 if self.client.following_count > FRIENDS_WATERMARK else 0 #WARNING: one extra db hit
		followers_weight = 1 if self.client.followers_count > FOLLOWERS_WATERMARK else 0
		comments_weight = 1 if self.comment_count > COMMENTS_WATERMARK else 0
	
		self.priority = friends_weight + followers_weight + comments_weight

		if write_to_db:
			try:
				self.save()
			except Exception, err:
				logger.critical(u"%s:%s" % (TAG, u"%s 更新豆瓣优先级失败，原因:%s" % (self, err)))               


create_doubanpost_success_signal.connect(create_doubanpost_success,
											sender=DoubanPost,
											weak=False, 
											dispatch_uid='signals.douban.create_doubanpost_success')


