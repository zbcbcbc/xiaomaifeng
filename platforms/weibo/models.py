# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
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
from weibo_python import *
from modelfields import *
from siteutils.comment import action_from_comment # reimport from xiaomaifeng_util


logger = logging.getLogger('xiaomaifeng.platforms')



class WeiboClientManager(ClientBaseManager):

	
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
		TAG = 'sinaweibo get authorize url'

		logger.info(u"%s:%s" % (TAG, u"新浪微博获取Authorize_url..."))

		url = sinaweibo_get_authorize_url(**kwargs)
		return url


	def create_authorized_weiboclient(self, user, code, create_on_success=True, **kwargs):
		'''
		如果成功返回结果，如果不成功，返回None
		不返回错误信息
		'''
		TAG = u'sinaweibo request access token and create'

		SUCCESS_MSG = u'用户连接微博成功'
		ERROR_MSG = u'用户连接微博失败，请稍后尝试或者联系客服'

		logger.info(u"%s:%s" % (TAG, u"%s尝试获取新浪微博Access Token..." % user))

		try:
			r = sinaweibo_request_access_token(code, **kwargs)
		except WeiboAPIError, err:
			logger.error(u"%s:%s" % (TAG, u"%s尝试获取新浪微博Access Token失败，原因:%s" % (user, err)))
			return (False, None, ERROR_MSG)           
		else:
			# 返回成功
			try:
				access_token = r['access_token']
				expires_in = r['expires_in']
				uid = r['uid']

				if create_on_success:
					client = WeiboClient(user=user, 
								access_token=access_token,
								uid=uid,
								social_platform=SocialPlatform.objects.get(name__exact='weibo'),
								expires_in=expires_in,
								add_date=djtimezone.now())
					status = client._get_client_info(write_to_db=False)
					if status:
						client.save(force_insert=True)
						return (True, client, SUCCESS_MSG)
					else:
						return (False, None, ERROR_MSG)
				else:
					return (True, r, None)

			except Exception, err:
				logger.critical(u"%s:%s" % (TAG, u"%s尝试获取微博access token失败，原因:%s" % (user,err)))
				return (False, None, ERROR_MSG)



# Check if auth has expired decorator
def weibo_auth2_required(func):

	def _weibo_auth2_required(self, *args, **kwargs):    
		if self.is_expires:
			logger.warning(u'%r sinaweibo oauth expired...' % self)  
			# TODO: try refresh access token
		return func(self, *args, **kwargs)
	return _weibo_auth2_required




class WeiboClient(SocialClientBase):
	'''
	API client using synchronized invocation.
	'''
	# 微博用户独有社交数据
	followers_count = models.PositiveIntegerField(default=0, null=False, editable=False)
	friends_count = models.PositiveIntegerField(default=0, null=False, editable=False)

	objects = WeiboClientManager()


	def __unicode__(self):
		return u"%s(%s)" % (self.user_name, self.pk)



	def update_priority(self, write_to_db=True, **kwargs):
		"""
		用法：计算出微博状态的优先级，优先级参数包括用户好友总数，跟随总数，微博评论总数， 微博转发总数
			0: 低优先级
			1: 中优先级
			2: 高优先级

		调和参数: FRIENDS_WATERMARK, VISITORS_WATERMARK, COMMENT_WATERMARK
			通过调整这3个参数，来调整人人状态优先级分布。

		"""
		TAG = 'weibo get priority'

		FRIENDS_WATERMARK = 300
		FOLLOWERS_WATERMARK = 300

		logger.info(u"%s:%s" % (TAG, u"%r updating priority..." % (self))) 

		friends_weight = 1 if self.friends_count > FRIENDS_WATERMARK else 0 #WARNING: one extra db hit
		followers_weight = 1 if self.followers_count > FOLLOWERS_WATERMARK else 0
		
	
		self.priority = friends_weight + followers_weight # STUB

		if write_to_db and self.id:
			try:
				self.save()
			except Exception, err:
				logger.critical(u"%s:%s" % (TAG, u"%r updating priority fail，reason:%s" % (self, err)))  



	def get_absolute_url(self):
		return reverse('platforms:weibo:client-detail', args=[str(self.id)])



	def _weiboAPI(self, path, method, **kwargs):
		"""
		如果出错, 抛出WeiboAPIError
		Subject to sinaweibo api change
		"""
		return sinaweibo_execute_api(self.access_token, path, method, **kwargs)



	def refresh_token(self):
		try:
			r = sinaweibo_refresh_token(self.refresh_token)
		except WeiboWeiboAPIError, err:
			print 'weibo refresh token err:', err


	@property
	def is_expires(self, write_to_db=True):
		"""
		查看微博用户授权是否过期
		如果数据没有保存到数据库，返回没有过期
		返回True/False
		"""
		EXPIRE_OFFSET = 60 # in seconds

		time_diff = (djtimezone.now() - self.add_date).total_seconds()
		self.expires_in -= time_diff
		if write_to_db: self.save() # TODO: hit db every time.
		r = not self.access_token or self.expires_in <= EXPIRE_OFFSET
		return r


	def _get_client_info(self, write_to_db=True, **kwargs):
		"""
		获取微博用户基本资料
		返回(状态)
		"""
		TAG = 'sinaweibo get client profile'

		logger.info(u"%s:%s" % (TAG, u'获取%r 资料中...' % self))

		try:
			path = 'users/show'
			method = 'GET'
			r = self._weiboAPI(path, method, uid=self.uid)
		except WeiboAPIError, err:
			# first: refresh token and call self
			if err.error_code == 21315 or err.error_code == 21327:
				logger.critical(u"%s weibo token expired, calling refresh_token..." % err.error_code)
				#self._refresh_token()
			#self._get_client_info(write_to_db=write_to_db, **kwargs)
				return False
			elif err.error_code == 'Weibo urllib2 URLError':
				logger.critical(u'Weibo urllib2 URLError')
				return False
			else:
				logger.error(u"%s:%s" % (TAG, u"更新%r 资料失败, 原因:%s" % (self, err)))
				return False
		else:
			try:
				self.user_name = r['screen_name']
				self.friends_count = r['friends_count']
				self.followers_count = r['followers_count']
				self.update_priority(write_to_db=False)
				if write_to_db: self.save()
				return True
			except Exception, err:
				logger.critical(u"%s:%s" % (TAG, u"%r获取基本资料失败, 原因:%s" % (self, err)))
				return False    



	#@weibo_auth2_required
	def update_client_profile(self, write_to_db=True, **kwargs):
		"""
		更新微博用户资料
		返回(状态，内容，信息)
		"""
		TAG = 'sinaweibo update client profile'
		logger.info(u"%s:%s" % (TAG, u'更新%r 资料中...' % self))

		try:
			path = 'users/show'
			method = 'GET'
			r = self._weiboAPI(path, method, uid=self.uid)
		except WeiboAPIError, err:
			# second: refresh token and call self
			if err.error_code == 21315 or err.error_code == 21327:
				logger.critical(u"%s weibo token expired, calling refresh_token..." % err.error_code)
				#self._refresh_token()
			#self.update_client_profile(write_to_db=write_to_db, **kwargs)
				return (False, None, None)
			elif err.error_code == 'Weibo urllib2 URLError':
				logger.critical(u'Weibo urllib2 URLError')
				return (False, None, None)
			else:
				logger.error(u"%s:%s" % (TAG, u"更新%r 资料失败, 原因:%s" % (self, err)))
				return (False, None, None)
		else:
			friends_count = r.get('friends_count', None)
			followers_count = r.get('followers_count', None)

			if friends_count: self.friends_count = friends_count
			if followers_count: self.followers_count = followers_count
			#WARNING 强制更新
			if friends_count and followers_count and write_to_db:
				try:
					self.update_priority(write_to_db=False)
					self.save(force_update=True) 
					return (True, None, u'微博用户资料更新成功')
				except Exception, err:
					logger.critical(u"%s:%s" % (TAG, u"%r更新详细资料失败, 原因:%s" % (self, err)))
					return (False, None, u'微博用户更新资料失败')                    



	#@weibo_auth2_required
	def create_post(self, merchandise, message=None, write_to_db=True, **kwargs):
		"""
		创建有照片或者无照片微博，若物品有照片则默认有照片微博
		返回tuple，(状态,内容，信息)
		注意：创建微博一定要在创建微博数据之前
		错误：如果创建微博后微博数据创建失败，则会使微博无效
		Database Transaction
		"""
		
		from dashboard.listing.models import Item, Fund

		TAG = 'sinaweibo create post'

		SUCCESS_MSG = u'用户发布到微博成功' #TODO
		ERROR_MSG = u'用户发布到微博失败'

		logger.info(u"%s:%s" % (TAG, u'%r 发布微博中...' % self))
		print u"weibo token is >>>> %s >>%s" %(self.access_token, self.refresh_token)
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
				# this is subject with image
				path = 'statuses/upload'
				method = 'POST'
				r = self._weiboAPI(path, method, status=status, pic=image)
			else:
				path = 'statuses/update'
				method = 'POST'
				# this content doesn't involve image
				r = self._weiboAPI(path, method, status=status) # throw WeiboAPIError
		except WeiboAPIError, err:
			# third: refresh token and call self
			if err.error_code == 21315 or err.error_code == 21327:
				logger.critical(u"%s weibo token expired, calling refresh_token..." % err.error_code)
				#self._refresh_token()
			#self.create_post(content,message=message,write_to_db=write_to_db, **kwargs)
				return (False, None,ERROR_MSG)
			elif err.error_code == 'Weibo urllib2 URLError':
				logger.critical(u'Weibo urllib2 URLError')
				return (False, None, ERROR_MSG)
			elif err.error_code == 20019:
				pass
			elif err.error_code == 200015: 
				# 账号、IP或应用非法，暂时无法完成此操作
				# 可以重新尝试
				pass
			logger.error(u"%s:%s" % (TAG, u"%r 发布微博失败，原因:%s" % (self, err)))
			return (False, None, ERROR_MSG)
		else:
			"""
			注意，Tightly coupled WeiboPost creation
			"""
			try:
				uid = r['user']['id']
				if str(uid) != str(self.uid):
					raise Exception(u"创建的微博用户%s和用户%s不符合" % (uid, self.uid))

				post = WeiboPost(merchandise_object=merchandise, 
								client_id=self.id, 
								pid=r['id'], 
								uid=uid,
								comment_count=r['comments_count'], 
								reposts_count=r['reposts_count'], 
								text=status,
								priority=self.priority)
				if write_to_db: post.save(force_insert=True) # 强制创建
				
				return (True, post, SUCCESS_MSG)

			except Exception, err:
				logger.critical(u"%s:%s" % (TAG, u"%r 创建WeiboPost失败，原因:%s" % (self, err)))
				return (False, None, ERROR_MSG)



	#@weibo_auth2_required
	def update_post(self, post, write_to_db=True, delete_on_notfound=True, **kwargs):
		"""
		更新微博信息，不包括评论
		如果没有在新浪微博上找到此条微博，选择默认永久删除此微博，不再刷新此微博状态
		返回(状态(Boolean)，内容(WeiboPost)，信息(String))
		"""
		TAG = 'weibo update post'

		SUCCESS_MSG = u'微博更新成功'
		ERROR_MSG = u'微博更新失败'

		logger.info(u"%s:%s" % (TAG, u'%r更新%r 中...是否写入数据库:%s, 没有找到是否删除:%s' % \
										(self, post, write_to_db, delete_on_notfound)))

		try:
			path = 'statuses/show'
			method = 'GET'
			r = self._weiboAPI(path, method, id=post.pid)
		except WeiboAPIError, err:
			# fourth: refresh token and call self
			if err.error_code == 21315 or err.error_code == 21327:
				logger.critical(u"%s weibo token expired, calling refresh_token..." % err.error_code)
				#self._refresh_token()
			#self.update_post(post,write_to_db=write_to_db, delete_on_notfound=delete_on_notfound, **kwargs)
				return (False, None, ERROR_MSG)
			elif err.error_code == 'Weibo urllib2 URLError':
				logger.critical(u'Weibo urllib2 URLError')
				return (False, None, ERROR_MSG)
			elif err.error_code == 10020 or err.error_code == 20101:
				# post not found on weibo!
				logger.warning(u"%s:%s" % (TAG, u"%r 更新%s 不存在" % (self, post)))

				if delete_on_notfound: post.delete() #WARNING

			logger.error(u"%s:%s" % (TAG, u"%r 更新%r 失败，原因:%s" % (self, post, err)))
			return (False, None, ERROR_MSG)
		else:
			try:
				uid = r['user']['id']
				if str(uid) != str(self.uid):
					logger.critical(u"%s:%s" % (TAG, u"%r更新%r失败，原因:%s" % (self, post, u'id are different?!')))
					post.delete() #WARNING
					raise Exception(u'微博拥有者id和微博用户id不符合')
				post.comment_count = r['comments_count']
				post.reposts_count = r['reposts_count']
				post.text = r['text']
				if write_to_db: post.save(force_update=True) #强制更新

				return (True, post, SUCCESS_MSG)
			except Exception, err:
				logger.critical(u"%s:%s" % (TAG, u"%r 读取%r 数据失败，原因:%s" % (self, post, err)))
				return (False, None, ERROR_MSG)

	def get_post_comments(self, post, since_id=None, **kwargs):
		"""
		根据某条微博找到所有大于since_id的微博评论
		速度性大于稳定性
		错误：未分别页面，在评论很多的情况可能出现评论未读取
			page 和 count 参数仍然没有得到官方文档的确认
			默认count = 50
			默认page = 1
		返回(内容(List))
			内容：list形式的评论，如错误返回空list,即返回0条评论
				返回list 的 评论id 应该从小到大，但是不能保证

		"""
		logger.info("getting %r'%r comments..." % (self, post))
		if str(post.uid) != str(self.uid):
			post.delete() #WARNING
			logger.critical("%r getting %r comments fail，err:%s" % (self, post, 'ids are different'))
			return []

		try:
			path = 'comments/show'
			method = 'GET'
			r = self._weiboAPI(path, method, id=post.pid, since_id=since_id or post.since_id, count=200)
			comments = r.get('comments', None)
			comments = list(comments) if comments else []
			# pass next_cursor alone
			next_cursor = r.get('next_cursor', 0)
			rt = {'comments':comments, 'next_cursor': next_cursor}
			return rt
		except WeiboAPIError, err:
			logger.error("%r getting %r comments fail，err:%s" % (self, post, err))
			return {}
# when urlerror happen, would get no comments from this




	@weibo_auth2_required
	def revoke_oauth2(self, **kwargs):
		"""
		驳回用户授权，此方法非常暴力，慎用
		返回(状态，内容，信息)
		"""
		TAG = u'sinaweibo revoke oauth2'
		logger.info(u"%s:%s" % (TAG, u'%r 驳回微博授权中...' % (self)))

		try:
			r = sinaweibo_revoke_oauth2(self.access_token)
			if 'result' not in r or r.result != 'true':
				logger.warning(u"%s:%s" % (TAG, u"%r 驳回微博授权失败，返回值:%s" % (self, r)))
				return (False, None, u'微博请求返回错误')
			else:
				return (True, None, None)
		except WeiboAPIError, err:
			logger.error(u"%s:%s" % (TAG, u"%r 驳回微博授权失败，原因:%s" % (self, err)))
			return (False, None, err)


	@weibo_auth2_required
	def end_session(self, **kwargs):
		"""
		结束用户session
		返回(状态，内容，信息)
		"""
		TAG = u'sinaweibo end session'
		logger.info(u"%s:%s" % (TAG, u'%r 终止微博Session中...' % (self)))

		try:
			path = 'account/end_session'
			method = 'GET'            
			r = self._weiboAPI(path, method, access_token=self.access_token)
			return (True, None, None)
		except WeiboAPIError, err:
			logger.error(u"%s:%s" % (TAG, u"%r 终止微博Session失败，原因:%s" % (self, err)))
			return (False, None, err)




class WeiboPostManager(SocialPostBaseManager):


	def poll_comments_fire_order(self, priority=1, since_id_storage=None):
		"""
		抓去微博评论并且下单
		注意：djcelery task logger 不太支持utf-8, encoding有bug, 用asci编码并且用英文log
				Mysql 不支持select_for_update(nowait=True) argument
		取消lock posts, database transaction 以加快速度
		回复列单由新到旧
		"""
		logger.warning("Find all weibo post and search for comemnts...")

		posts = self.all() #TODO suppose to filter by priority. Post is cached here

		# iterate over posts
		for post in posts:
			# assign post storage key
			post_storage_key = "weibo%s" % post.id
			# 获取comments
			seller_weiboclient = post.client #TODO: what if weibo client doesn't exist any more? Receiver's WeiboClient is cached here
			# 同时获取db 和 storage 储存的since_id, 比较出最大的避免重复filter comment
			cur_since_id_post = post.since_id
			cur_since_id_storage = since_id_storage.get(post_storage_key) or 0 if since_id_storage else 0 # 避免None
			cur_since_id = int(max(cur_since_id_post, cur_since_id_storage))

			# initial comment as a list
			comments = []
			temp = seller_weiboclient.get_post_comments(post)
			comments_temp = temp.get('comments',[])
			next_cursor = temp.get('next_cursor',0)
			# make sure there is at least one comment
			if comments_temp != []:
				while True:
					for k in comments_temp:
						# if id is smaller (older) than the current id, break
						if k['id'] <= cur_since_id:
							break
						comments.append(k)
					#print u"%s weibo_new_comment" %k['text'] # debuggin
					# if next page's id is smaller (older) than the current id, break
					if next_cursor <= cur_since_id:
						break
					temp = seller_weiboclient.get_post_comments(post, since_id=next_cursor) #TODO:chain them in celery? should never fail or throw error
					comments_temp = temp['comments']
					next_cursor = temp['next_cursor']
			# the return is empty, no comment at all

			for comment in comments:
				# 从comment中读取关键数据, 如果任意数据读取失败则忽视此评论
				comment_id = int(comment.get('id', None))
				text = comment.get('text', None)
				comment_user = comment.get('user', None)
				comment_user_id = comment_user.get('id', None) if comment_user else None

				if not comment_id or not text or not comment_user_id:
					logger.critical('%r Weibo reply key error' % post)
					pass

				elif comment_user_id == seller_weiboclient.user_id:
					logger.warning("Seller and Buyer are the same person, ignore this comment")
					pass

				else:
					if comment_id <= cur_since_id:
						logger.warning("This comment(%s) is a repeat comment, ignore it" % comment_id)
						pass
					else:
						# 有效的comment_id, 从用户评论判定用户行为
						action, amount = action_from_comment(text)
						if action == 'buy':
							buyer_weiboclient = WeiboClient.objects.get_unique_or_none(uid=comment_user_id) #Cache payer_weiboclient here
							if buyer_weiboclient:
								# 用户在网站注册过
								buyer = buyer_weiboclient.user #WARNING
								seller = seller_weiboclient.user #WARNING
								social_platform = buyer_weiboclient.social_platform
								body = post.text
								merchandise = post.merchandise_object
								quantity = int(amount)
								create_order_task.apply_async(args=[buyer, seller, text, social_platform, body, merchandise, quantity])
							else:
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
					
			# Endfor -> comments loop
			post.since_id = cur_since_id
			post.save(force_update=True)
			logger.warning("update since_id:%s" % post.since_id)
			logger.warning("%r update success" % post)
			#TODO: 危险，如果since_id没有save,则会导致重复下单
		


class WeiboPost(SocialPostBase):

	#微博帐户
	client = models.ForeignKey(WeiboClient, null=False, on_delete=models.CASCADE, editable=False)
	# 微博独有的相关信息
	reposts_count = models.PositiveIntegerField(default=0, null=False, editable=False)

	objects = WeiboPostManager()



	class Meta(SocialPostBase.Meta):
		unique_together = (('merchandise_id', 'client', 'merchandise_type'),)


	def __unicode__(self):
		return u"WeiboPost(%s): %s" % (self.pk, self.text)



			 


create_weibopost_success_signal.connect(create_weibopost_success, 
											sender=WeiboPost, 
											weak=False, 
											dispatch_uid='signals.weibo.create_weibopost_success')



