# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng

__author__ = "Bicheng Zhang, Jian Chen "
__copyright__ = "Copyright 2013, XiaoMaiFeng"




import time, logging

from django.utils import timezone as djtimezone
from django.db import models, connection
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, post_save, post_delete
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import IntegrityError
from django.core.urlresolvers import reverse
from django.db.models import F


from siteutils.comment import action_from_comment # TODO from xiaomaifeng_utils instead
from dashboard.orders.tasks import create_order_task
from platforms.models import *
from signals import *
from signal_handlers import *
from renren_python import *
from modelfields import *




logger = logging.getLogger('xiaomaifeng.platforms')



class RenrenClientManager(ClientBaseManager):


    def get_authorize_url(self, redirect_uri=None, mac=False, **kwargs):
        """
        No error should raise here
        支持mac认证和Bearer认证，默认Bearer认证
        #TODO: cache url
        """

        url = get_renren_authorize_url(mac=mac, **kwargs)
        return url


    def create_authorized_renrenclient(self, user, code, mac=False, create_on_success=True, **kwargs):
        """
        Capture errors here
        """
        TAG = u'create authorized renrenclient'

        SUCCESS_MSG = u'用户连接人人成功'
        ERROR_MSG = u'用户连接人人失败，请稍后尝试或者联系客服'

        logger.info(u"%s:%s" % (TAG, u"%r尝试获取Access Token..." % user))

        try:
            r = request_renren_access_token(code, mac, **kwargs)
        except RenRenAPIError, err:
            logger.error(u"%s:%s" % (TAG, u"%r尝试获取人人Access Token失败，原因:%s" % (user, err)))
            return (False, None, ERROR_MSG)
        else:
            try:
                access_token = r['access_token']
                #mac_key = r['mac_key']
                refresh_token = r['refresh_token']
                expires_in = r['expires_in']
                uid = r['user']['id']

                # update or create
                client = RenrenClient(user=user, 
                                access_token=access_token,
                                refresh_token=refresh_token,
                                expires_in=expires_in,
                                add_date=djtimezone.now(),
                                social_platform=SocialPlatform.objects.get(name__exact='renren'),
                                uid=uid,) #TODO
                                #mac_key=mac_key)
                status = client._get_client_info(write_to_db=False)
                if status:
                    client.save(force_insert=True)
                    return (True, client, SUCCESS_MSG)    
                else:
                    return (False, None, ERROR_MSG)
            except Exception, err:
                logger.critical(u"%s:%s" % (TAG, u"%r创建帐户失败，原因:%s" % (user, err)))
                return (False, None, ERROR_MSG)    




# Check if auth has expired decorator
def renren_auth2_required(func):

    def _renren_auth2_required(self, *args, **kwargs):    
        if self.is_expires:
            logger.warning(u'%r授权过期' % self)
        return func(self, *args, **kwargs)
    return _renren_auth2_required



class RenrenClient(SocialClientBase):

    # 人人用户独有连接数据
    mac_key = models.CharField(max_length=255, null=True, editable=False)

    # 人人帐户独有信息
    visitor_count = models.PositiveIntegerField(default=0, null=False, editable=False)
    friend_count = models.PositiveIntegerField(default=0, null=False, editable=False)

    objects = RenrenClientManager()


    class Meta(SocialClientBase.Meta):
        permissions = (
            ('can_create_renren_album',u'可以创建人人相册'),
        )


    def __unicode__(self):
        return u"%s(%s)" % (self.user_name, self.pk)



    def update_priority(self, write_to_db=True, **kwargs):
        """
        用法：计算出人人状态的优先级，优先级参数包括用户好友总数，来访总数，和状态评论总数
        公式: friends_count > 0 --> 0, friends_count > 500 --> 1
            visitors_count > 0 --> 0, visitors_count > 5000 --> 1
            comment_count > 0 --> 0, comment_count > 100 --> 1
        0: 低优先级
        1: 中优先级
        2: 高优先级

        调和参数: FRIENDS_WATERMARK, VISITORS_WATERMARK, COMMENT_WATERMARK
        通过调整这3个参数，来调整人人状态优先级分布。

        """
        TAG = u'renren get priority'

        logger.info(u"%s:%s" % (TAG, u'%r updating priority...' % (self))) 

        FRIENDS_WATERMARK = 500
        VISITORS_WATERMARK = 5000
        if not self.friend_count or not self.visitor_count:
            self.priority = 1 # 默认返回中优先级
        else:
            friends_weight = 1 if self.friend_count > 500 else 0 #WARNING: extra db hit
            visitors_weight = 1 if self.visitor_count > 500 else 0
            self.priority = friends_weight + visitors_weight
        if write_to_db and self.id:
            #If this is not first created and write to db is True.
            try:
                self.save()
            except Exception, err:
                logger.critical(u"%s:%s" % (TAG, u"%r updating priority fail，reaon:%s" % (self, err))) 


    def get_absolute_url(self):
        return reverse('platforms:renren:client-detail', args=[str(self.id)])
        


    def _renrenAPI(self, path, method, **kwargs):
        """
        Raise renren API error
        """
        return renren_http_call(self.access_token, path, method, mac_key=self.mac_key, **kwargs)

    def _refresh_token(self):
        try:
            logger.info(u"refreshing token >>>")
            r = renren_refresh_token(self.refresh_token)
        except RenrenAPIError, err:
            # !!!!!!!!!! deal with this !!!!!!!
            print 'renren refresh token err:', err
        else:
            logger.info(u"store new token info >>")
            self.access_token = r['access_token']
            self.expires_in = r['expires_in']
            self.refresh_token = r['refresh_token']
            self.add_date = djtimezone.now()
            self.save()

    @property
    def is_expires(self):
        """
        查看人人用户授权是否过期, 只有在Bearer authorization时才生效
        """
        TAG = 'renren is expires'

        if self.mac_key:
            return False
        #logger.info(u"%s:%s" % (TAG, u"%s检查人人授权是否过期..." % self))

        EXPIRE_OFFSET = 60 # in seconds

        time_diff = (djtimezone.now() - self.add_date).total_seconds()
        self.expires_in -= time_diff
        r = not self.access_token or self.expires_in <= EXPIRE_OFFSET
        return r


    def _get_client_info(self, write_to_db=True, **kwargs):
        """
        获取人人网用户基本资料
        返回(状态(Boolean))
        """

        TAG = 'renren update client profile'

        logger.info(u"%s:%s" % (TAG, u'获取%r 资料中...' % self))

        path = "/v2/user/get"
        method = "GET"

        try:
            r = self._renrenAPI(path, method, userId=self.uid)
        except RenRenAPIError, err:
# ????? fuck renren!!!! invalid_authorization.EXPIRED-TOKEN ?? (code, message, status_code)
# "message":"Access Token\u65e0\u6548\u3002","code":"invalid_authorization.INVALID-TOKEN"
            # first
            if err.error_code == 'invalid_authorization.EXPIRED-TOKEN' or err.error_code == 'EXPIRED-TOKEN':
                logger.info(u"%s renren token expired, calling refresh" % err.error_code)
                self._refresh_token()
                self._get_client_info(write_to_db=write_to_db, **kwargs)
            else:
                logger.error(u"%s:%s" % (TAG, u"获取%r 基本资料失败, 原因:%s" % (self, err)))
                return False
        else:
            try:
                self.user_name = r['name']
                self.update_priority()
                if write_to_db: self.save() # create or update
                return True
            except Exception, err:
                logger.error(u"%s:%s" % (TAG, u"%r 保存人人帐户基本数据失败, 原因:%s" % (self, err)))
                return False
            
        

    #@renren_auth2_required
    def update_client_profile(self, write_to_db=True, **kwargs):
        """
        更新人人网用户主页详细资料
        返回(状态，内容，信息)
        """

        TAG = 'renren update client profile'

        SUCCESS_MSG = u'人人用户资料更新成功'
        ERROR_MSG = u'人人用户资料更新失败'

        logger.info(u"%s:%s" % (TAG, u'更新%r 详细资料中...' % self))

        path = "/v2/user/get"
        method = "GET"

        try:
            r = self._renrenAPI(path, method, userId=self.uid)
        except RenRenAPIError, err:
            # second
            if err.error_code == 'invalid_authorization.EXPIRED-TOKEN' or err.error_code == 'EXPIRED-TOKEN':
                logger.info(u"%s renren token expired, calling refresh" % err.error_code)
                self._refresh_token()
                self.update_client_profile(write_to_db=write_to_db, **kwargs)
            else:
                logger.error(u"%s:%s" % (TAG, u"更新%r详细资料失败, 原因:%s" % (self, err)))
                return (False, None, ERROR_MSG)
        else:
            try:
                self.visitor_count = r['visitorCount']
                self.friend_count = r['friendCount']
                self.update_priority(write_to_db=False)
                if write_to_db: self.save(force_update=True) # Force update
                return (True, None, SUCCESS_MSG)
            except Exception, err:
                logger.error(u"%s:%s" % (TAG, u"更新%r详细资料失败, 原因:%s" % (self, err)))
                return (False, None, ERROR_MSG)



    #@renren_auth2_required
    def create_post(self, merchandise, message=None, write_to_db=True, **kwargs):
        """
        创建状态, 物品的照片直接被忽略
        返回tuple, (状态，内容，信息)
        """

        TAG = 'renren create post'

        SUCCESS_MSG = u'用户发布到人人成功' #TODO
        ERROR_MSG = u'用户发布到人人失败'

        logger.info(u"%s:%s" % (TAG, u'%r 发布状态中...' % self))

        from dashboard.listing.models import Item, Fund
        # initiate status message
        if isinstance(merchandise, Item):
            text = message or merchandise.description
            text += u' #小麥蜂 #出售'
        elif isinstance(merchandise, Fund):
            text = message or merchandise.description
            text += u' #小麥蜂 #集资'
        else:
            logger.critical(u"%s:%s" % (TAG, u"%r 发布物品:%r 无法识别" % (self, merchandise)))
            return (False, None, ERROR_MSG)

        # initiate params
        path = '/v2/status/put'
        method = 'POST'
        try:
            r = self._renrenAPI(path, method, content=text)
        except RenRenAPIError, err:
            # third
            if err.error_code == 'invalid_authorization.EXPIRED-TOKEN' or err.error_code == 'EXPIRED-TOKEN':
                logger.info(u"%s renren token expired, calling refresh" % err.error_code)
                self._refresh_token()
                self.create_post(merchandise, message=message, write_to_db=write_to_db, **kwargs)
            else:
                logger.error(u"%s:%s" % (TAG, u"%r 发布状态失败，原因:%s" % (self, err)))
                return (False, None, ERROR_MSG)
        else:
            try:
                pid = r['id']
                commentCount = r['commentCount']
                uid = r['ownerId']
                text = r['content']
                createTime = r['createTime']

                post = RenrenPost(client=self,
                                pid=pid, 
                                uid=uid,
                                merchandise_object=merchandise,
                                comment_count=commentCount,
                                text=text)
                                #priority=priority)
                if write_to_db: post.save() # force_create=true
                return (True, post, SUCCESS_MSG)
            except Exception, err:
                logger.critical(u"%s:%s" % (TAG, u"%r 创建状态数据失败，原因:%s" % (self, err)))
                return (False, None, ERROR_MSG)
            
            


    #@renren_auth2_required
    def create_photo_post(self, merchandise, aid, message=None, **kwargs):
        """
        物品图片post一定要post到传入aid的相册id内
        人人后台目前不支持图片上传
        返回tuple, (状态，内容，信息)
        """
        TAG = 'renren create photopost'
        logger.info(u"%s:%s" % (TAG, u'%r 发布照片中...' % self))

        from dashboard.listing.models import Item, Fund
        # initiate status message
        if isinstance(merchandise, Item):
            text = message or merchandise.description + u' #小麥蜂 #出售'
        elif isinstance(merchandise, Fund):
            text = message or merchandise.description + u' #小麥蜂 #集资'
        else:
            logger.critical(u"%s:%s" % (TAG, u"%r 发布物品:%r 无法识别" % (self, merchandise)))
            return (False, None, u'发布物品无法识别')

        # initiate params
        image = open(merchandise.image.path,'rb')

        path = '/v2/photo/upload'
        method = 'POST'

        try:
            r = self._renrenAPI(path, method, albumId=aid, description=text, file=image)
        except RenRenAPIError, err:
            # fourth
            if err.error_code == 'invalid_authorization.EXPIRED-TOKEN' or err.error_code == 'EXPIRED-TOKEN':
                logger.info(u"%s renren token expired, calling refresh" % err.error_code)
                self._refresh_token()
                self.create_photo_post(merchandise, aid, message=message, **kwargs)
            else:
                print u"%s:%s"  % (TAG, err)
                return (False, None, err)
        else:
            #print r
            pid = r['id']
            aid = r['albumId']
            uid = r['ownerId']
            text = r['description']
            view_count = r['viewCount']

            # whether to use a new renren post post model, 
            # or reuse renren post to accomodate is the question
            try:
                post = RenrenPost(client=self,
                                    pid=pid,
                                    text=text,
                                    uid=uid,
                                    merchandise_object=merchandise,
                                    view_count=view_count,
                                    post_type='photo')
                post.save()
                return (True, None, u'用户发布人人照片成功')
            except IntegrityError, err:
                logger.error(u"%s:%s" % (TAG, u"%r 创建状态数据失败，原因:%s" % (self, err)))
                return (False, None, err)

    #@renren_auth2_required
    def update_post(self, post, write_to_db=True, delete_on_notfound=True, **kwargs):
        """
        更新状态资料
        返回tuple, (状态，内容, 信息)
        """
        TAG = 'renren update post'

        SUCCESS_MSG = u'人人状态更新成功'
        ERROR_MSG = u'人人状态更新失败'

        logger.info(u"%s:%s" % (TAG, u'%r更新%r 中...是否写入数据库:%s, 没有找到是否删除:%s' % \
                                        (self, post, write_to_db, delete_on_notfound)))

        
        # path is different for photo post and status post
        method = 'GET'

        try:
            if post.post_type == 'photo':
                path = '/v2/photo/get' #photoId instead of statusId
                r = self._renrenAPI(path, method, photoId=post.pid, ownerId=self.uid)
            else:
                path = '/v2/status/get'
                r = self._renrenAPI(path, method, statusId=post.pid, ownerId=self.uid)
        except RenRenAPIError, err:
            # fifth
            if err.error_code == 'EXPIRED-TOKEN' or err.error_code == 'invalid_authorization.EXPIRED-TOKEN':
                logger.info(u"%s renren token expired, calling refresh" % err.error_code)
                self._refresh_token()
                self.update_post(post, write_to_db=write_to_db, delete_on_notfound = delete_on_notfound, **kwargs)
            else:
            
                logger.error(u"%s:%s" % (TAG, u"%r updating%r failed，原因:%s" % (self, post, err)))
                #TODO: detech which kind of failure is not found
                if delete_on_notfound: post.delete()
            
                return (False, None, ERROR_MSG)
        else:
            post.comment_count = r.get('commentCount', 0)
            post.forward_count = r.get('shareCount', 0)
            post.text = r.get('content', None)
            post.save()
            return (True, None, SUCCESS_MSG)

            
                          
    #@renren_auth2_required !!
    def get_post_comments(self, post, since_id=None, **kwargs):
        """
        得到某状态的所有评论,
        返回(内容(List))
            内容：List形式的评论列表
        错误：未支持分页和count
        相册：默认page =1, count=20, order为最新到旧
        若返回错误，返回空List,默认为返回0条评论
        """

        TAG = u'renren get post comments'

        logger.info(u"%s:%s" % (TAG, u'%r 获取%r 评论中...' % (self, post)))

        path = '/v2/comment/list'
        method = 'GET'       

        if post.uid != self.uid:
            # 检查是否属于同一个人人帐户
            logger.critical(u"%s:%s" % (TAG, u"%r 获取%r 评论失败，原因:%s" % (self, post, u'self.uid and post.uid are different')))
            return []

        # check if pageNumber is specified, and get the commentType
        pageNumber = kwargs.get('pageNumber',1)
        commentType = kwargs.get('commentType')
        try:
            r = self._renrenAPI(path, method, entryOwnerId=self.uid, entryId=post.pid, pageSize=100, pageNumber=pageNumber, commentType=commentType)
            r = list(r) if r else []
				#print 'renrenrenrenren:',r #for debugging
            return r
        except RenRenAPIError, err:
            logger.error(u"%s:%s" % (TAG, u"%r 获取%r 评论失败，原因:%s" % (self, post, err)))
            return []




    #@renren_auth2_required
    def get_album_list(self, **kwargs):
        """
        返回用户相册列表
        已列表形势返回所有数据, 出错则返回空列表
        返回(状态，内容，信息)
        """
        TAG = u'renren get album list'

        SUCCESS_MSG = u'人人获取相册列表成功'
        ERROR_MSG = u'人人获取相册列表失败'

        logger.info(u"%s:%s" % (TAG, u'%r 获取相册列表中...' % (self)))

        path = '/v2/album/list'
        method = 'GET'   

        try:
            r = self._renrenAPI(path, method, ownerId=self.uid)
        except RenRenAPIError, err:
            logger.error(u"%s:%s" % (TAG, u"%r 获取相册列表失败，原因:%s" % (self, err)))
            return (False, None, ERROR_MSG)
        else:
            r = list(r)
            return (True, r, SUCCESS_MSG)





class RenrenPostManager(SocialPostBaseManager):


    def poll_comments_fire_order(self, priority=1, since_id_storage=None):
        """
        找出所有人人Post
        并且在每个post下找出所有自从since_id的人人评论
        取消lock posts以加快速度
		回复由新到旧
        """
        
        logger.warning("Find all renren post and search for comemnts...")

        posts = self.all() #TODO suppose to filter by priority, Post is cached here
        for post in posts:
            post_storage_key = "renren%s" % post.id
            # 获取comments
            seller_renrenclient = post.client
            post_type = post.post_type
            # 同时获取db 和 storage 储存的since_id, 比较出最大的避免重复filter comment
            cur_since_id_post = post.since_id
            cur_since_id_storage = since_id_storage.get(post_storage_key) or 0 if since_id_storage else 0 # 避免None
            cur_since_id = int(max(cur_since_id_post, cur_since_id_storage))


            # initialize comments as a list
            comments = []
            # getting comments for renren status
            flag = 0
            pageNumber = 1
            comments_temp = seller_renrenclient.get_post_comments(post, commentType='STATUS' if post_type=='status' else 'PHOTO')

            # when comments_temp is not empty, and there is more pageNumber
            while comments_temp != []:
                for k in comments_temp:

                    if k['id'] <= cur_since_id : # at the beginning, cur_since_id would be 0, add a if condition check if it was 0
                        flag = 1
                        break
                    comments.append(k)
                #print u"%s renren_new_comment" %k['content'] # debuggin
                if flag == 1:
                    break
                pageNumber = pageNumber + 1
                comments_temp = seller_renrenclient.get_post_comments(post, pageNumber=pageNumber, commentType='STATUS' if post_type=='status' else 'PHOTO')



            for comment in comments:
                # 从comment中读取关键数据, 如果任意数据读取失败则忽视此评论
                comment_id = int(comment.get('id', None))
                comment_user_id = comment.get('authorId', None)
                created_at = comment.get('time', None)
                text = comment.get('content', None)

                if not comment_id or not comment_user_id or not text:
                    logger.warning("%r Renren reply key error" % post)
                    pass

                elif comment_user_id == seller_renrenclient.user_id:
                    logger.warning("Buyer and seller are the same person, ignore this comment")
                    pass

                else:
                    if comment_id <= cur_since_id:
                        logger.warning("This comment(%s) is a repeat comment, ignore it" % comment_id)
                        pass
                    else:
                        # 有效的comment_id, 判定用户行为
                        action, amount = action_from_comment(text)
                        if action == 'buy':
                            buyer_renrenclient = RenrenClient.objects.get_unique_or_none(uid=comment_user_id) #Cache buyer_renrenclient here
                            if buyer_renrenclient:
                                buyer = buyer_renrenclient.user #WARNING
                                seller = seller_renrenclient.user #WARNING
                                social_platform = buyer_renrenclient.social_platform
                                body = post.text#post.message
                                merchandise = post.merchandise_object
                                quantity = int(amount) if amount else 0
                                
                                create_order_task.apply_async(args=[buyer, seller, text, social_platform, body, merchandise, quantity])
                            else:
                                # 用户没有在网站注册
                                logger.warning("Comment user is not a website resigstered user")

                                pass
                            #endif 判定用户是否在网站注册
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



class RenrenPost(SocialPostBase):

    # 主要信息
    client = models.ForeignKey(RenrenClient, on_delete=models.CASCADE)
    # 人人网独有信息
    post_type = models.CharField(max_length=10, null=False, default='status', editable=False)
    view_count = models.PositiveIntegerField(default=0, null=False, editable=False)
    share_count = models.PositiveIntegerField(default=0, null=False, editable=False)

    objects = RenrenPostManager()

    

    class Meta(SocialPostBase.Meta):
        unique_together = (('merchandise_id', 'client', 'merchandise_type'),)


    def __unicode__(self):
        return u"%r(%s):%s" % (RenrenPost, self.id, self.text)

 




create_renrenpost_success_signal.connect(create_renrenpost_success, 
                                            sender=RenrenPost, 
                                            weak=False, 
                                            dispatch_uid='signals.renren.create_renrenpost_success')





