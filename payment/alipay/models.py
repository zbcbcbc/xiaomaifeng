# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



import urllib, datetime, logging
from urllib import urlencode, urlopen

from django.conf import settings
from django.utils import timezone as djtimezone
from django.db import models, connection, IntegrityError
from django.db.models.signals import pre_delete, post_save, post_delete
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from siteutils.signalutils import receiver_subclasses
from dashboard.listing.models import Item, Fund, DigitalItem, PhysicalItem, DonationFund, PaybackFund, EventItem
from signals import *
from payment.signals import payment_verify_success_signal, shippment_confirm_success_signal
from signal_handlers import *
from platforms.alipay.alipay_python import *
from platforms.alipay.modelfields import *
from payment.alipay.modelfields import *
from payment.models import *



logger = logging.getLogger('xiaomaifeng.payment')


# 网关地址
_GATEWAY = 'https://www.alipay.com/cooperate/gateway.do?'



class AlipayPartnerTradeManager(PartnerTradeBaseManager):


	def create_payment(self, xmf_order, buyer, seller, body, item, price, quantity, logistics_fee, total_fee):
		"""
		payer, receiver, item, 都已经从Database读取并且cache
		利用Python Exception机制换来更稳定，明了的判定方式
		"""
		logger.warning('creating alipay partner trade payment...')

		print u'准备用户支付宝信息...'
		try:
			seller_alipay_id = 2088121212121212 #SUB receiver.alipayclient.alipay_user_id
		except:
			return (None, '卖家支付宝帐号读取失败')

		try:
			buyer_alipay_id = 2088212121212121 #STUB payer.alipayclient.alipay_user_id
		except:
			return (None, '买家支付宝帐号读取失败')

		subject = item.description

		if isinstance(item, PhysicalItem):
			# 准备物流信息
			logistics_type = item.logistics_type
			logistics_payment = item.logistics_payment

			# 准备收货用户信息
			receive_name = buyer.userprofile.fullname
			receive_address = buyer.userprofile.fulladdress
			receive_zip = buyer.userprofile.zip_code
			receive_mobile = buyer.userprofile.mobile
			if not receive_name or not receive_address or not receive_zip or not receive_mobile:
				return (None, '用户资料填写不完整,无法实行实体物品交易,请把资料填写完整')


		elif isinstance(item, (EventItem, DigitalItem,)):
			# 虚拟物品
			logistics_type = 'DIRECT' # 无需物流
			logistics_payment = 'BUYER_PAY'
			receive_name = buyer.userprofile.fullname or None
			receive_address = buyer.userprofile.fulladdress or None
			receive_zip = buyer.userprofile.zip_code or None
			receive_mobile =  buyer.userprofile.mobile or None

		else:
			return (None, '此商品不符合规格，请避免购买此物品')

		print 'creating alipay partnertrade....'

		try:
			payment = self.create(xmf_order=xmf_order,
									body=body,
									logistics_type=logistics_type,
									logistics_fee=logistics_fee,
									logistics_payment=logistics_payment,
									subject=subject, # subject should be available in comment
									quantity=quantity, # quantity should be available in comment
									price=price,
									total_fee=1, #TODO
									discount=0, #TODO
									seller_alipay_id=seller_alipay_id,
									buyer_alipay_id=buyer_alipay_id,
									# should add user emails to add safety
									receive_name=receive_name, #TODO
									receive_address=receive_address, #TODO
									receive_zip=receive_zip, #TODO
									receive_mobile=receive_mobile)

			return (payment, None)

		except Exception, err:
			logger.warning("%r fail:%s" % (self, err))
			return (None, err)


	def verify_payment(self, params):
		"""
		处理支付宝担保交易交易同步返回结果，
		通常是用户认证交易,付款结束后返回结果
		返回处理结果: status(Boolean)
		"""

		logger.info(u"%s处理同步返回结果中..." % self)

		# 基本参数      
		is_success = params['is_success'] # String(1) 表示接口调用是否成功,并不表明业务处理结果。
		partnerId = params['partnerId'] # String(16) 签约的支付宝账号对应的支付宝唯一用户号。以 2088 开头的 16 位纯数字组成。
		sign_type = params['sign_type'] # String
		sign= params['sign'] # String(32)
		charset = params['charset'] # 商户网站使用的编码格式,如 utf-8、gbk、gb2312 等。

		# 业务参数
		# --通知参数
		notify_id = params['notify_id'] # String 支付宝通知校验 ID,商户可以 用这个流水号询问支付宝该条 通知的合法性。
		notify_type = params['notify_type'] # String 返回通知类型。交易状态改变时发送的同步通知。
		notify_time = params['notify_time'] # Date 通知时间(支付宝时间)。格式为 yyyy-MM-dd HH:mm:ss。

		# 交易参数
		trade_no = params['trade_no'] # String(64) 该交易在支付宝系统中的交易流水号。最短16位,最长64位。
		out_trade_no = params('out_trade_no', None) # String(64) 对应商户网站的订单系统中的 唯一订单号,非支付宝交易号。需保证在商户网站中的唯一性。是请求时对应的参数,原样返回。
		trade_status = params['trade_status'] # 取值范围请参见附录“11.5 交易 状态”。
		gmt_create = params('gmt_create', None) # Date 该笔交易创建的时间。格式为 yyyy-MM-dd HH:mm:ss。

		# 商品参数
		subject = params['subject'] # String(256) 商品的标题/交易标题/订单标题/订 单关键字等。
		price = params['price'] # 单位为:RMB Yuan。取值范围为 [0.01,1000000.00],精确到小数 点后两位。
		quantity = params['quantity'] # 商品的数量。
		body = params('body', None) # String(400) 对一笔交易的具体描述信息。 如果是多种商品,请将商品描 述字符串累加传给 body。

		# 交易双方用户支付宝参数
		seller_email =params['seller_email'] # String 登录时,seller_email 和 seller_id 两者必填一个。
		buyer_email =params['buyer_email'] # String 买家支付宝账号。
		seller_id = params['seller_id'] # String 卖家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数字。登录时,seller_email 和 seller_id 两者必填一个。
		buyer_id = params['buyer_id'] # String 买家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数字。

		# 收费参数
		payment_type = params('payment_type', None) # 收款类型,只支持 1:商品购买。
		is_total_fee_adjust = params['is_total_fee_adjust'] # String(1) 该交易是否调整过价格。
		use_coupon = params['use_coupon'] # String(1) 是否在交易过程中使用了红包。
		discount = params['discount'] # 支付宝系统会把 discount 的 值加到交易金额上,如果需要 折扣,本参数为负数。
		total_fee = params['total_fee'] # 单笔交易金总额,单位为 RMB-Yuan。取值范围为[0.01, 1000000.00],精确到小数点后两 位。
		gmt_payment = params('gmt_payment', None) # Date 该笔交易的买家付款时间。格式为 yyyy-MM-dd HH:mm:ss   

		# 物流参数
		logistics_type = params('logistics_type', None) # String
		logistics_fee = params('logistics_fee', None) # String
		logistics_payment = params('logistics_payment', None) # String
		gmt_logistics_modify = params('gmt_logistics_modify', None) # String 物流状态更改时间

		# 动作参数
		buyer_actions = params('buyer_actions', None) # String 买家动作集合
		seller_actions = params('seller_actions', None) # String 卖家动作集合

		# 退款参数
		refund_status = params('refund_status', None) # Date 取值范围请参见“12.4 退款 状态”
		gmt_refund = params('gmt_refund', None) # 卖家退款的时间,退款通知时 会发送。格式为 yyyy-MM-dd HH:mm:ss。


		# 收款人详细信息
		receive_name = params('receive_name', None)
		receive_address = params('receive_address', None)
		receive_zip = params('receive_zip', None)
		receive_phone = params('receive_phone', None)
		receive_mobile = params('receive_mobile', None)   

		logger.info(u"%s处理同步返回结果完成" % self)

		#TODO: if True, send verify_success signal and save is_verified to True
		return False #STUB     



	def update_payment(self, params):
		"""
		处理支付宝担保交易交易异步返回结果，
		通常是更新Order信息，更新用户行为
		返回处理结果: status(Boolean)
		"""

		logger.info(u"%s处理异步返回结果中..." % self)

		# 基本参数  
		notify_id = params('notify_id') # String 支付宝通知校验 ID,商户可以 用这个流水号询问支付宝该条 通知的合法性。
		notify_type = params('notify_type') # String 返回通知类型。交易状态改变时发送的同步通知。
		notify_time = params('notify_time') # Date 通知时间(支付宝时间)。格式为 yyyy-MM-dd HH:mm:ss。
		sign_type = params('sign_type') # String
		sign= params('sign') # String(32)

		# 业务参数
		# --交易参数
		trade_no = params('trade_no') # String(64) 该交易在支付宝系统中的交易流水号。最短16位,最长64位。
		trade_status = params('trade_status') # 取值范围请参见附录“11.5 交易 状态”。
		body = params('body', None) # String(400) 对一笔交易的具体描述信息。 如果是多种商品,请将商品描 述字符串累加传给 body。
		out_trade_no = params('out_trade_no', None) # String(64) 对应商户网站的订单系统中的 唯一订单号,非支付宝交易号。需保证在商户网站中的唯一性。是请求时对应的参数,原样返回。
		gmt_create = params('gmt_create', None) # Date 该笔交易创建的时间。格式为 yyyy-MM-dd HH:mm:ss。

		# 商品参数
		subject = params('subject') # String(256) 商品的标题/交易标题/订单标题/订 单关键字等。
		price = params('price') # 单位为:RMB Yuan。取值范围为 [0.01,1000000.00],精确到小数 点后两位。
		quantity = params('quantity') # 商品的数量。

		# 交易双方用户支付宝参数
		seller_email =params('seller_email') # String 登录时,seller_email 和 seller_id 两者必填一个。
		buyer_email =params('buyer_email') # String 买家支付宝账号。
		seller_id = params('seller_id') # String 卖家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数字。登录时,seller_email 和 seller_id 两者必填一个。
		buyer_id = params('buyer_id') # String 买家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数字	

		# 费用参数
		total_fee = params('total_fee') # 单笔交易金总额,单位为 RMB-Yuan。取值范围为[0.01, 1000000.00],精确到小数点后两 位。
		discount = params('discount') # 支付宝系统会把 discount 的 值加到交易金额上,如果需要 折扣,本参数为负数。
		use_coupon = params('use_coupon') # String(1) 是否在交易过程中使用了红包。
		is_total_fee_adjust = params('is_total_fee_adjust') # String(1) 该交易是否调整过价格。
		payment_type = params('payment_type', None) # 收款类型,只支持 1:商品购买。
		gmt_payment = params('gmt_payment', None) # Date 该笔交易的买家付款时间。格式为 yyyy-MM-dd HH:mm:ss 

		# 物流参数
		logistics_type = params('logistics_type', None) # String
		logistics_fee = params('logistics_fee', None) # String
		logistics_payment = params('logistics_payment', None) # String
		gmt_logistics_modify = params('gmt_logistics_modify', None) # String 物流状态更改时间

		# 动作参数
		buyer_actions = params('buyer_actions', None) # String 买家动作集合
		seller_actions = params('seller_actions', None) # String 卖家动作集合

		# 退款参数
		refund_status = params('refund_status', None) # Date 取值范围请参见“12.4 退款 状态”
		gmt_refund = params('gmt_refund', None) # 卖家退款的时间,退款通知时 会发送。格式为 yyyy-MM-dd HH:mm:ss。


		# 收款人详细信息
		receive_name = params('receive_name', None)
		receive_address = params('receive_address', None)
		receive_zip = params('receive_zip', None)
		receive_phone = params('receive_phone', None)
		receive_mobile = params('receive_mobile', None) 

		logger.info(u"%s处理异步返回结果完成" % self)

		return False


class AlipayPartnerTrade(PartnerTradeBaseModel):
	"""
	支付宝纯担保交易数据模型
	时间皆为支付宝时间
	TODO: 联系支付宝配置关闭时间
	"""
	"""
	交易参数
	"""

	# 以下必须填写
	token = AlipayUserTokenField(null=True, editable=False) # TODO: 此token在实际应用中为必须填写，因为用户将通过 如果开通了快捷登录产品,则需要 填写;如果没有开通,则为空。

	# 以下选择性填写
	body = models.TextField(max_length=400, null=True, editable=True) # String(400) 对一笔交易的具体描述信 息。如果是多种商品,请将 商品描述字符串累加传给 body

	# 以下verify后才得到更新
	trade_status = models.CharField(max_length=200, null=True, editable=True) # String 交易目前所处的状态。成功状态的值只有两个: TRADE_FINISHED(普通 即时到账的交易成功状态)
	trade_no = AlipayTradeNoField(unique=True, null=True, editable=False)
	gmt_create = AlipayDateTimeField(null=True, editable=True) # Date 该笔交易创建的时间。格式为 yyyy-MM-dd HH:mm:ss。

	"""
	物流参数
	物流信息: 物流信息中最多可以传三组物流信息,第一组的物流信息参数是不可缺少的必 填参数,
				每组三个物流信息(logistics_type、logistics_fee、logistics_payment) 不可缺少任一项,
				必须有第一组才能有第二组,有第二组才能有第三组,且不 能与第一组物流方式中的物流类型相同,
				通过这种方式,合作伙伴可以传递多 种物流选择方式供买家选择。
	"""
	# 以下必须填写
	logistics_type = AlipayLogisticsTypeField(max_length=100, null=False, editable=True) # String, 第一组物流类型。取值范围请参见附录 “11.3 物流类型”
	logistics_fee = AlipayLogisticsFeeField(null=False, editable=True) # TODO: 设置物流价格区间 String, 第一组物流运费。单位为:RMB Yuan。精确 到小数点后两位。缺省值为 0 元。 
	logistics_payment = AlipayLogisticsPaymentField(max_length=100, default='BUYER_PAY', null=False, editable=True) # String, 第一组物流支付类型。取值范围请参见附录 “11.4 物流支付类型”。

	# 以下verify后才得到更新
	gmt_logistics_modify = AlipayDateTimeField(null=True, editable=True)# String 物流状态更改时间
	
	"""
	商品参数
	"""
	# 以下必须填写
	subject = AlipaySubjectField(null=False, editable=True) # String(256) 商品的标题/交易标题/订单 标题/订单关键字等。
	quantity = models.PositiveIntegerField(null=False, editable=True) # TODO: 设置物品量区间
	price = AlipayPriceField(null=False, editable=True)
	

	"""
	收费参数
	"""
	# 以下必须填写
	payment_type = models.CharField(max_length=4, default='1', null=False, editable=True)# String(4) 收款类型,只支持 1:商品购 买。
	# 以下选择填写
	total_fee = AlipayTotalFeeField(null=True, editable=True)
	discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, editable=True) # 支付宝系统会把 discount 的 值加到交易金额上,如果需 要折扣,本参数为负数。单位为:RMB Yuan,精确到 小数点后两位。缺省值为 0 元。
   
	# 以下verify后才得到更新 
	gmt_payment = AlipayDateTimeField(null=True, editable=True)
	use_coupon = models.CharField(max_length=1, default='N', null=True, editable=True)

	"""
	交易双方信息参数
	"""
	# 以下必须填写
	seller_email = models.EmailField(max_length=100, null=False, editable=True)# String(100), 卖家支付宝账号。卖家信息优先级:seller_id>seller_account_name> seller_email。seller_id,seller_account_name 和 seller_email 不能全部为空,至 少有一项不为空
	
	# 以下选择填写
	buyer_email = models.EmailField(max_length=100, null=True, editable=True)# String(100), 买家支付宝账号。买家信息优先级:buyer_id>buyer_account_name> buyer_email。
	seller_alipay_id = AlipayUserIdField(null=True, editable=True) # 卖家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数 字。登录时,seller_email 和 seller_id 两者必填一个。
	buyer_alipay_id = AlipayUserIdField(null=True, editable=True) # 买家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数 字。

	"""
	收款人详细信息
	"""
	# 以下选择填写, 皆可为空
	receive_name = AlipayReceiverNameField(null=True, editable=True)
	receive_address = AlipayReceiverAddressField(null=True, editable=True)
	receive_zip = AlipayReceiverZipField(null=True, editable=True)
	receive_mobile = AlipayReceiverMobileField(null=True, editable=True)


	"""
	退款参数
	"""
	# 以下verify后开始退款才得到更新
	gmt_refund = AlipayDateTimeField(null=True, editable=True)
	refund_status = models.CharField(max_length=50, null=True, editable=True)


	"""
	寄货参数
	"""
	logistics_name = AlipayLogisticsNameField(null=True, editable=True)
	invoice_no = models.CharField(max_length=32, null=True, editable=True)
	transport_type = models.CharField(max_length=50, null=True, editable=True)
	seller_ip = models.CharField(max_length=15, null=True, editable=True)


	"""
	认证,过期
	"""
	verify_url = models.URLField(max_length=2000, null=True, editable=False)
	it_b_pay = models.SmallIntegerField(default=12, null=False, editable=True) # 普通用户默认12小时过期

	objects = AlipayPartnerTradeManager()


	def __unicode__(self):
		return u"%s(%s)" % (self.body, self.pk)

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)


	def save(self, *args, **kwargs):
		# Tight couple to ensure item reservation is correct
		"""
		注意：必须call save来reserve物品，避免bulk operation
		TODO: put in signal， 避免逻辑tight coupled
		
		if not self.id:
			reserve_success = False
			#if this is the first time to create
			if self.is_reserved:
				# !启动物品预留机制
				logger.info(u"%s启动物品预留机制..." % self)
				try:
					self.content_object.do_reserve(self.quantity)
					reserve_success = True
					logger.info(u"%s预留%s, 数量%s 成功..." % (self, self.content_object, self.quantity))
				except Exception, err:
					logger.warning(u"%s预留%s, 数量%s失败，原因:%s" % (self, self.content_object, self.quantity, err))
					raise IntegrityError(u'物品无法预留,数量不够') #TODO Item reservation error
			try:
				super(AlipayPartnerTrade, self).save(*args, **kwargs)
			except Exception, err:
				if self.is_reserved and reserve_success:
					self.content_object.undo_reserve(self.quantity) # This method will not fail
					logger.error(u"撤销预留%s, 数量%s, 原因:%s" % (self, self.content_object, self.quantity, err))
				raise
		else:
			# this is not the first time to create
		"""
		super(AlipayPartnerTrade, self).save(*args, **kwargs)

	

	@property
	def has_confirmed_shipping(self):
		"""
		检查卖家是否已经确认寄出
		"""
		if self.trade_status == 'WAIT_BUYER_CONFIRM_GOODS' or self.trade_status == 'TRADE_FINISHED':
			return True
		else:
			return False


	def build_verify_url(self, write_to_db=False, **kwargs):
		"""
		纯担保交易接口
		功能描述: 纯担保交易提供的功能为:
				以支付宝为第三方担保,保证买卖双方在交易的过程中, 
				买家能收到货,卖家能收到钱。
				其交易流程是:“买家付款”→“卖家发货”→“买 家确认收货”→“卖家确认收款”。
		"""

		logger.info(u"%r building verify url ..." % self)
		#print u"%r building verify url ..." % self

		params = {}

		"""
		必须填写基本参数
		"""
		params['service']       = 'create_partner_trade_by_buyer' # 接口名称。
		params['partner']           = ALIPAY_PARTNER # String(16)
		params['_input_charset']    = ALIPAY_INPUT_CHARSET # String

		#print 'must basic data prepare finished..'
		"""
		可空基本参数
		"""
		params['notify_url']        = ALIPAY_NOTIFY_URL # String, 支付宝服务器主动通知商户 网站里指定的页面 http 路径
		params['return_url']        = ALIPAY_RETURN_URL # String, 支付宝处理完请求后,当前 页面自动跳转到商户网站里 指定页面的 http 路径。

		#print 'optional basic data prepare finished...'
		"""
		必须填写业务参数
		"""
		params['out_trade_no']  = self.xmf_order_id      # String(64), 支付宝合作商户网站唯一订单号(确保在合作伙伴系统中唯一)。
		params['subject']       = self.subject   # String(256) 商品的标题/交易标题/订单 标题/订单关键字等。
		params['payment_type']  = self.payment_type # String, 收款类型,只支持 1:商品购 买。
		params['price'] = self.price             # Number, 单位为:RMB Yuan。取值 范围为 [0.01,1000000.00],精确 到小数点后两位。
		params['quantity'] = self.quantity              # Number, 商品的数量
		params['seller_id']      = self.seller_alipay_id # String(100) 登录时,seller_email 和 seller_id 两者必填一个。

		#print 'must business data prepare finished'
		"""
		物流信息: 物流信息中最多可以传三组物流信息,第一组的物流信息参数是不可缺少的必 填参数,
				每组三个物流信息(logistics_type、logistics_fee、logistics_payment) 不可缺少任一项,
				必须有第一组才能有第二组,有第二组才能有第三组,且不 能与第一组物流方式中的物流类型相同,
				通过这种方式,合作伙伴可以传递多 种物流选择方式供买家选择。
		"""
		params['logistics_type'] = self.logistics_type   # String, 第一组物流类型。取值范围请参见附录 “11.3 物流类型”。
		params['logistics_fee'] = self.logistics_fee # String, 第一组物流运费。单位为:RMB Yuan。精确 到小数点后两位。缺省值为 0 元。  
		params['logistics_payment'] = self.logistics_payment # String, 第一组物流支付类型。取值范围请参见附录 “11.4 物流支付类型”。

		#print 'logistics data prepare finished...'
		"""
		可空业务参数,但是网站定义为必填
		"""
		params['buyer_id'] = self.buyer_alipay_id # String(30) 买家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数 字。可空
		params['body']          = self.body      #String(400) 对一笔交易的具体描述信 息。如果是多种商品,请将 商品描述字符串累加传给 body
		params['show_url'] = self.xmf_order.merchandise_object.show_url # String(400) 收银台页面上,商品展示的超链接。
		params['total_fee'] = self.total_fee # 该笔订单的资金总额,单位为 RMB-Yuan。取值范围为[0.01, 100000000.00],精确到小数点后 两位。Number
		params['discount'] = self.discount # 支付宝系统会把 discount 的 值加到交易金额上,如果需 要折扣,本参数为负数。单位为:RMB Yuan,精确到 小数点后两位。缺省值为 0 元。
		
		#print 'must/optional business data prepare finished...'

		if self.receive_name:
			params['receive_name'] = self.receive_name # String(128) 收货人姓名。
		if self.receive_address:
			params['receive_address'] = self.receive_address # String(256) 收货人地址。
		if self.receive_zip:
			params['receive_zip'] = self.receive_zip # String(20) 收货人邮编。
		if self.receive_mobile:
			params['receive_mobile'] = self.receive_mobile # String 收货人手机

		#print 'receiver data prepare finished...'
		"""
		只有开通了自定义超时功能,设置的请求参数 t_s_send_1、t_s_send_2、t_b_rec_post、it_b_pay 才有效。
		 
		params['it_b_pay'] = '' # 设置未付款交易的超时时 间,一旦超时,该笔交易就 会自动被关闭。取值范围:1m~15d。m-分钟,h-小时,d-天,1c- 当天(无论交易何时创建, 都在 0 点关闭)。该参数数值不接受小数点, 如 1.5h,可转换为 90m。该功能需要联系支付宝配置关闭时间。
		params['t_s_send_1'] = '' # 卖家逾期不发货,允许买家 退款的期限。如果商户未设置支持自定义超时,该参数应该为空,否则会报错。单位为天(d)。
		params['t_s_send_2'] = '' # 卖家逾期不发货,建议买家 退款。如果商户未设置支持自定义超时,该参数应该为空,否则会报错。单位为天(d)。
		params['t_b_rec_post'] = '' # 买家逾期不确认收货,自动 完成交易(平邮)的期限。如果商户未设置支持自定义超时,该参数应该为空,否则会报错。单位为天(d)。
		""" 

		"""
		只有开通了快捷登录,才能使用请求参数 token(授权 令牌码),且必须设置 token。
		"""
		params['token'] = self.token # String(40) 如果开通了快捷登录产品,则需要填写;如果没有开通,则为空
		#print 'token prepare finished...'

		params,prestr = params_filter(params)
	
		params['sign'] = build_mysign(prestr, ALIPAY_KEY, ALIPAY_SIGN_TYPE)
		params['sign_type'] = ALIPAY_SIGN_TYPE

		#print 'data signed...'
	
		url = _GATEWAY + urlencode(params)   

		logger.info(u"%r finised building verify url: %s" % (self, url))
		#print u"%r finised building verify url: %s" % (self, url)
		#print len(url)

		if write_to_db:
			self.verify_url = url
			self.save(force_update=True)

		return url


	def build_shippment_confirm_url(self, auto_send=False, **kwargs):
		"""
		支付宝确认发货接口

		注意：
			1.此接口只支持https请求;

			2.在交易类型是支付宝担保交易时,如果交易状态是“买家已付款,等待卖家发
				货(交易状态参数 trade_status 值为 WAIT_SELLER_SEND_GOODS)”的 
				情况下确认发货接口才执行成功;如果交易状态不是“买家已付款,
				等待卖家 发货”或“卖家已发货,等待买家确认”的情况下确认发货都将失败;

			3.如果本交易为COD交易,则交易状态为“等待卖家发货”或者“等待买家签收 
				付款”的情况下确认发货才执行成功;
				如果交易状态不是“等待卖家发货”或 
				“等待买家签收付款”的情况下确认发货都将失败;

			4.在担保交易或COD交易的接口中,如果设置了请求参数notify_url,
				那么执行 了确认发货接口后,担保交易接口或 COD 交易接口的 notify_url 对应页面文件 
				会收到支付宝的发货通知。具体通知内容根据对应接口的通知信息而定。
		"""

		logger.info(u"%s创建确认发货Url中..." % self)

		params = {}

		# 必须填写的基本参数
		params['service']       = 'send_goods_confirm_by_platform' # 接口名称
		params['partner']           = ALIPAY_PARTNER # 签约的支付宝账号对应的支付宝唯一用户号。以 2088 开头的 16 位纯数字 组成。
		params['_input_charset']    = ALIPAY_INPUT_CHARSET # 商户网站使用的编码格式,如 utf-8、gbk、gb2312 等。

		#必须填写的业务参数
		params['trade_no']  = self.trade_no # 支付宝根据商户请求,创建订 单生成的支付宝交易号。最短16位,最长64位。String(64)
		params['logistics_name'] = self.logistics_name   # 物流公司名称, 不可空 String(64)

		#可空的业务参数
		if self.transport_type:
			params['transport_type'] = self.transport_type # 取值范围请参见附录“9.4 物流类型”。create_transport_type 和 transport_type 不能同时为 空。
		if self.invoice_no:
			params['invoice_no'] = self.invoice_no # 物流发货单号。 String(32)
		if self.seller_ip:
			params['seller_ip'] = self.seller_ip # 卖家本地电脑 IP 地址(非局 域网 IP 地址)。 String(15)

		params,prestr = params_filter(params)
	
		params['sign'] = build_mysign(prestr, ALIPAY_KEY, ALIPAY_SIGN_TYPE)
		params['sign_type'] = ALIPAY_SIGN_TYPE
	
		url = _GATEWAY + urlencode(params)

		logger.info(u"%s创建确认发货Url成功, url:%s" % (self, url))

		if auto_send:
			# 自动发送货物寄送确认，
			# STUB
			pass

		return url


	def shippment_confirm(self):
		"""
		确认物品寄出逻辑
		"""
		#STUB
		#print 'calling shippment_confirm_succeess...'
		self._shippment_confirm_success()


	def _verify_success(self, **kwargs):
		"""
		支付宝担保交易认证成功逻辑:
			如果认证成功，发送认证成功信号
		"""
		try:
			if self.is_verified:
				raise Exception('%r is verified already' % self)

			self.is_verified = True
			self.save(force_update=True)
			payment_verify_success_signal.send_robust(sender=self.__class__, payment=self)

		except Exception, err:
			logger.critical('%r verify success error:%s' % (self, err))


	def _verify_fail(self, reason, re_verify=True, **kwargs):
		"""
		支付宝担保交易认证成功逻辑:
			如果认证成功，发送认证失败信号
		"""		
		payment_verify_fail_signal.send(sender=self.__class__, 
												payment=self,
												reason=reason,
												re_verify=re_verify)

	def _shippment_confirm_success(self, **kwargs):
		"""
		支付宝担保交易认证物品寄出成功逻辑：
			如果认证成功，发送认证成功信号
		"""
		#print 'sending shippment confirm signal...'
		shippment_confirm_success_signal.send_robust(sender=self.__class__, payment=self)		


	def _shippment_confirm_fail(self, reason, re_verify=True, **kwargs):
		"""
		支付宝担保交易认证物品寄出成功逻辑：
			如果认证成功，发送认证成功信号
		"""
		alipay_goodsent_fail_signal.send(sender=self.__class__,
											instance=self,
											reason=reason,
											re_verify=re_verify)


from dashboard.orders.signal_handlers import order_payment_verify_success_handler, \
							order_shippment_confirm_success_handler

# 连接支付宝担保交易认证成功信号
payment_verify_success_signal.connect(order_payment_verify_success_handler, 
					sender=AlipayPartnerTrade,
					weak=False, 
					dispatch_uid="alipay.signals.partnertrade_payment_verify_success")



# 连接支付宝寄货认证成功信号
shippment_confirm_success_signal.connect(order_shippment_confirm_success_handler,
					sender=AlipayPartnerTrade,
					weak=False, 
					dispatch_uid="alipay.signals.partnertrade_shippment_confirm_success")







class AlipayDirectPayManager(DirectPayBaseManager):


	def create_payment(self, xmf_order, buyer, seller, body, fund, total_fee):
		"""
		payer, receiver, item, 都已经从Database读取并且cache
		利用Python Exception机制换来更稳定，明了的判定方式
		"""
		logger.warning('creating alipay direct pay order...')


		print 'prepareing user alipay account info...'
		try:
			seller_alipay_id = 2088121212121233 #SUB receiver.alipayclient.alipay_user_id
		except:
			return (None, u"卖家支付宝帐号读取失败")

		try:
			buyer_alipay_id = 2088121212121244 #STUB payer.alipayclient.alipay_user_id
		except:
			return (None, '买家支付宝帐号读取失败')


		print  u'preparing fund info...'
		if isinstance(fund, DonationFund):
			# 捐款类筹资
			payment_type = '4'
			payment_method = 'directpay'
		elif isinstance(fund, PaybackFund):
			# 普通筹资
			payment_type = '1'
			payment_method = 'directpay'
		else:
			return (None, u"此商品不符合规格，请避免购买此筹资")				

		subject = fund.description

		print 'creating directpay order...'
		try:
			payment = self.create(xmf_order=xmf_order,
								body=body,
								payment_type=payment_type,
								paymethod=payment_method,
								total_fee=total_fee,
								seller_alipay_id=seller_alipay_id,
								buyer_alipay_id=buyer_alipay_id,
								subject=subject)

			return (payment, None)

			
		except Exception, err:
			logger.critical(u"%r hard fail, reason:%s" % (self, err))
			return (None, err)

	def handle_return_url_data(self, params):
		"""
		处理支付宝及时到账交易同步返回结果，
		通常是用户认证交易结果
		返回处理结果: status(Boolean)
		"""
		logger.info(u"%s处理同步返回结果中..." % (self))

		# 基本参数      
		is_success = params['is_success'] # String(1) 表示接口调用是否成功,并不表明业务处理结果。
		sign_type = params['sign_type'] # String
		sign= params['sign'] # String(32)

		# 业务参数
		# －－交易参数
		out_trade_no = params('out_trade_no', None) # String(64) 对应商户网站的订单系统中的 唯一订单号,非支付宝交易号。需保证在商户网站中的唯一性。是请求时对应的参数,原样返回。
		trade_no = params('trade_no', None) # String(64) 该交易在支付宝系统中的交易流水号。最短16位,最长64位。
		trade_status = params('trade_status', None) # String 交易目前所处的状态。成功状态的值只有两个: TRADE_FINISHED(普通 即时到账的交易成功状态)
		body = params('body', None) # String(400) 对一笔交易的具体描述信息。 如果是多种商品,请将商品描 述字符串累加传给 body。       


		# 商品参数
		subject = params('subject', None) # String(256) 商品的标题/交易标题/订单标 题/订单关键字等。

		# 收费参数
		payment_type = params('payment_type', None) # String(4) 对应请求时的 payment_type 参数,原样返回。
		total_fee = params('total_fee', None) # 该笔订单的资金总额,单位为 RMB-Yuan。取值范围为[0.01, 100000000.00],精确到小数点 后两位。

		# 通知参数
		notify_id = params('notify_id', None) # String 支付宝通知校验 ID,商户可以 用这个流水号询问支付宝该条 通知的合法性。
		notify_time = params('notify_time', None) # Date 通知时间(支付宝时间)。格式为 yyyy-MM-dd HH:mm:ss。
		notify_type = params('notify_type', None) # String 返回通知类型。
		
		# 交易双方用户支付宝参数
		seller_email =params('seller_email', None) # String(100) 卖家支付宝账号,可以是 Email 或手机号码。
		buyer_email =params('buyer_email', None) # String(100) 买家支付宝账号,可以是 Email 或手机号码。
		seller_id = params('seller_id', None) # String(30) 卖家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数字。
		buyer_id = params('buyer_id', None) # String(30) 买家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数字。        
		
		# 调用参数
		exterface = params('payment_type', None) # 标志调用哪个接口返回的链接。

		logger.info(u"%s处理同步返回完成..." % (self))

		return False #STUB



	def handle_notify_url_data(self, params):
		"""
		处理支付宝及时到账交易异步返回结果，
		通常是更新Order数据，用户对Order的行为更新
		返回处理结果: status(Boolean)
		"""

		logger.info(u"%s处理异步返回结果中..." % (self))

		# 基本参数
		#  -- 通知参数
		notify_time = params('notify_time') # Date 通知时间(支付宝时间)。格式为 yyyy-MM-dd HH:mm:ss。
		notify_type = params('notify_type') # String 返回通知类型。
		notify_id = params['notify_id'] # String 通知校验 ID。
		sign_type = params['sign_type'] # String
		sign= params['sign'] # String

		# 业务参数
		# --交易参数
		out_trade_no = params('out_trade_no', None) # String(64) 对应商户网站的订单系统中的 唯一订单号,非支付宝交易号。需保证在商户网站中的唯一性。是请求时对应的参数,原样返回。
		trade_no = params('trade_no', None) # String(64) 该交易在支付宝系统中的交易流水号。最短16位,最长64位。
		trade_status = params('trade_status', None) # String 交易目前所处的状态。成功状态的值只有两个: TRADE_FINISHED(普通 即时到账的交易成功状态)
		gmt_create = params('gmt_create', None) # Date 该笔交易创建的时间。格式为 yyyy-MM-dd HH:mm:ss。
		gmt_close =params('gmt_close', None) # Date 交易关闭时间。格式为 yyyy-MM-dd HH:mm:ss。
		body = params('body', None) # String(400) 该笔订单的备注、描述、明细 等。对应请求时的 body 参数,原 样通知回来。


		# 商品参数
		subject = params('subject', None) # String(256) 商品的标题/交易标题/订单 标题/订单关键字等。它在支付宝的交易明细中排 在第一列,对于财务对账尤为 重要。是请求时对应的参数, 原样通知回来。
		#price = params('price', None) # 如果请求时使用的是 total_fee,那么 price 等于 total_fee;如果请求时使用的 是 price,那么对应请求时的 price 参数,原样通知回来。
		total_fee = params('total_fee', None) # 该笔订单的总金额。请求时对应的参数,原样通知 回来。
		#quantity = params('quantity', None) # 如果请求时使用的是 total_fee,那么 quantity 等于 1;如果请求时使用的是 quantity,那么对应请求时的 quantity 参数,原样通知回 来。

		# 费用参数
		payment_type = params('payment_type', None) # String(4) 对应请求时的 payment_type 参数,原样返回。
		is_total_fee_adjust = params('is_total_fee_adjust', None) # String(1) 该交易是否调整过价格。
		use_coupon = params('use_coupon', None) # String(1) 是否在交易过程中使用了红包。
		gmt_payment = params('gmt_payment', None) # Date 该笔交易的买家付款时间。格式为 yyyy-MM-dd HH:mm:ss
			
		# 退款参数
		gmt_refund = params('gmt_refund', None) #  Date 卖家退款的时间,退款通知时 会发送。格式为 yyyy-MM-dd HH:mm:ss。
		refund_status = params('refund_status', None) # 取值范围请参见“12.4 退款 状态”

		# 交易双方用户支付宝信息
		seller_email =params('seller_email', None) # String(100) 卖家支付宝账号,可以是 Email 或手机号码。
		buyer_email =params('buyer_email', None) # String(100) 买家支付宝账号,可以是 Email 或手机号码。
		seller_id = params('seller_id', None) # String(30) 卖家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数字。
		buyer_id = params('buyer_id', None) # String(30) 买家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数字。

		logger.info(u"%s处理异步返回结果完成" % (self))

		return False #STUB


class AlipayDirectPay(DirectPayBaseModel):
	"""
	支付宝及时到账数据模型
	时间皆为支付宝时间
	"""

	"""
	交易参数
	"""
	
	# 以下选择性填写
	body = models.TextField(max_length=1000, null=True, editable=True) # String(1000) 对一笔交易的具体描述信息。如果 是多种商品,请将商品描述字符串 累加传给 body。
	token = AlipayUserTokenField(null=True, editable=False) # 此token在实际应用中为必须填写，因为用户将通过 如果开通了快捷登录产品,则需要 填写;如果没有开通,则为空。

	# 以下verify后才得到更新
	trade_no = AlipayTradeNoField(max_length=64, null=True)
	trade_status = models.CharField(max_length=200, null=True, editable=True) # String 交易目前所处的状态。成功状态的值只有两个: TRADE_FINISHED(普通 即时到账的交易成功状态)
	gmt_create = AlipayDateTimeField(null=True, editable=True) # Date 该笔交易创建的时间。
	gmt_close = AlipayDateTimeField(null=True, editable=True) # Date 交易关闭时间。

	"""
	收费参数
	"""
	# 以下必须填写
	payment_type = models.CharField(max_length=4, null=False, editable=True)# String(4) 取值范围请参见附录“12.6 收款 类型”。默认值为:1(商品购买)。 4(捐赠)
	paymethod = models.CharField(max_length=10, default='directPay', editable=True) # 取值范围: creditPay(信用支付), directPay(余额支付), 如果不设置,默认识别为余额支付
	total_fee = AlipayTotalFeeField(null=True, editable=True) # 该笔订单的资金总额,单位为 RMB-Yuan。取值范围为[0.01, 100000000.00],精确到小数点后 两位。Number
	
	# 以下verify后才得到更新
	gmt_payment = AlipayDateTimeField(null=True, editable=True)

	"""
	交易双方用户信息
	"""
	# 以下选择性填写 (email or id 必须填写一个)
	seller_email = models.EmailField(max_length=100, null=True, editable=True)# String(100), 卖家支付宝账号。卖家信息优先级:seller_id>seller_account_name> seller_email。seller_id,seller_account_name 和 seller_email 不能全部为空,至 少有一项不为空
	buyer_email = models.EmailField(max_length=100, null=True, editable=True)# String(100), 买家支付宝账号。买家信息优先级:buyer_id>buyer_account_name> buyer_email。
	seller_alipay_id = AlipayUserIdField(null=True, editable=True) # String(16) 卖家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数 字。登录时,seller_email 和 seller_id 两者必填一个。
	buyer_alipay_id = AlipayUserIdField(null=True, editable=True) # String(16) 买家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数 字。
	

	"""
	商品信息
	"""
	# 以下必须填写
	subject = AlipaySubjectField(null=False, editable=True) # String(256) 商品的标题/交易标题/订单标题/订 单关键字等。该参数最长为 128 个汉字。 
	
	

	"""
	退款参数
	"""
	# 以下verify后退款生效后才得到更新
	gmt_refund = AlipayDateTimeField(null=True, editable=False)
	refund_status = models.CharField(max_length=50, null=True, editable=False)


	"""
	认证Url
	"""
	verify_url = models.URLField(max_length=2000, null=True, editable=False)

	objects = AlipayDirectPayManager()



	def __unicode__(self):
		return u"%s(%s)" % (self.body, self.pk)


	def get_absolute_url(self):
		return reverse('payment:alipay:directpay-detail', args=[str(self.pk)])



	def build_verify_url(self, write_to_db=False, **kwargs):
		"""
		功能描述：通过支付宝的支付渠道,付款者可以直接汇款给另一个拥有支付宝账号的收款者。
		不返回
		#WARNING: IN DEVELOPMENT
		"""
		logger.info(u"%r building verify url..." % self)

		params = {}
		# 必须填写基本参数
		params['service']       = 'create_direct_pay_by_user' # 接口名称。
		params['partner']           = ALIPAY_PARTNER # 签约的支付宝账号对应的支付宝唯一用户号。以 2088 开头的 16 位纯数字组成。String(1 6)
		params['_input_charset']    = ALIPAY_INPUT_CHARSET # 

		# 可空基本参数
		params['return_url']        = ALIPAY_RETURN_URL # 支付宝处理完请求后,当前页面自 动跳转到商户网站里指定页面的 http 路径。String(2 00)
		params['notify_url']        = ALIPAY_NOTIFY_URL  # 支付宝服务器主动通知商户网站 里指定的页面 http 路径。String(1 90)
		params['error_notify_url'] = '' # 当商户通过该接口发起请求时,如 果出现提示报错,支付宝会根据 “12.7 item_orders_info出错时 的通知错误码”和“12.8 请求出 错时的通知错误码”通过异步的方 式发送通知给商户。该功能需要联系支付宝开通。String(2 00)

		# 必须填写业务参数
		params['out_trade_no']  = self.xmf_order_id      # 支付宝合作商户网站唯一订单号 String(6 4) 
		params['subject']       = self.subject   # 商品的标题/交易标题/订单标题/订 单关键字等。该参数最长为 128 个汉字。 String(2 56)
		params['payment_type']  = self.payment_type # 取值范围请参见附录“12.6 收款 类型”。默认值为:1(商品购买)。 注意:支付类型为“47”时,公共业务扩 展参数(extend_param)中必须 包含凭证号 (evoucheprod_evouche_id)参 数名和参数值。String(4)
		params['seller_id'] = self.seller_alipay_id # 卖家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数 字。登录时,seller_email 和 seller_id 两者必填一个。可空 String(3 0)
		params['buyer_id'] = self.buyer_alipay_id # 买家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数 字。可空
		params['total_fee'] = self.total_fee # 该笔订单的资金总额,单位为 RMB-Yuan。取值范围为[0.01, 100000000.00],精确到小数点后 两位。Number
		params['body']          = self.body      # 对一笔交易的具体描述信息。如果 是多种商品,请将商品描述字符串 累加传给 body。String(1 000)
		params['paymethod'] = self.paymethod   # 取值范围: creditPay(信用支付), directPay(余额支付), 如果不设置,默认识别为余额支付。String
		params['show_url']          = self.xmf_order.merchandise_object.show_url # String(4 00) 收银台页面上,商品展示的超链接。
   

		params['need_ctu_check'] = '' # 商户在配置了支持 CTU(支付宝风 险稽查系统)校验权限的前提下, 可以选择本次交易是否需要经过 CTU 校验。Y:做, N:不做
		params['defaultbank'] = ''          # 默认网银代号，代号列表见http://club.alipay.com/read.php?tid=8681379

		# 扩展功能参数——分润
		params['royalty_type'] = '10'   # 目前只支持一种类型:10(卖家给 第三方提成)
		params['royalty_parameters'] = '' # String(1 000) 详细请见备注 

		# 扩展功能参数——防钓鱼
		params['anti_phishing_key'] = '' # 通过时间戳查询接口获取的加密支付宝系统时间戳。如果已申请开通防钓鱼时间戳验证,则此字段必填。
		params['exter_invoke_ip'] = ''

		# 其他参数
		params['exter_invoke_ip'] = '' # 用户在创建交易时,该用户当前所 使用机器的 IP。如果商户申请后台开通防钓鱼 IP 地址检查选项,此字段必填,校验 用。String(1 5)
	
		# 扩展功能参数——自定义参数
		params['extra_common_param'] = '' # 如果用户请求时传递了该参数,则 返回给商户时会回传该参数。String(1 00)
		params['extend_param'] = '' # 用于商户的特定业务信息的传递, 只有商户与支付宝约定了传递此 参数且约定了参数含义,此参数才 有效。

		# 扩展功能－超时
		params['it_b_pay'] = '' # 设置未付款交易的超时时 间,一旦超时,该笔交易就 会自动被关闭。取值范围:1m~15d。m-分钟,h-小时,d-天,1c- 当天(无论交易何时创建, 都在 0 点关闭)。该参数数值不接受小数点, 如 1.5h,可转换为 90m。该功能需要联系支付宝配置关闭时间。

		# 扩展功能－自动登陆
		params['default_login'] = '' # String, 用于标识商户是否使用自动登录 的流程。如果和参数 buyer_email 一起使用时,就不会再让用户登录 支付宝,即在收银台中不会出现登 录页面. Y:用,N:不用
	
		# 扩展功能－商户产品类型
		params['product_type'] = '' # String(50), 用于针对不同的产品,采取不同的 计费策略。如果开通了航旅垂直搜索平台产 品,请填写 CHANNEL_FAST_PAY;如果没 有,则为空。

		# 扩展功能－快捷登陆
		params['token'] = order.token
	
		params,prestr = params_filter(params)
	
		params['sign'] = build_mysign(prestr, ALIPAY_KEY, ALIPAY_SIGN_TYPE)
		params['sign_type'] = ALIPAY_SIGN_TYPE
		
		url = _GATEWAY + urlencode(params)

		logger.info(u"%r finished building verify url:%s" % (self, url))

		if write_to_db:
			self.verify_url = url
			self.save(force_update=True)

		return url



	def _verify_success(self, **kwargs):
		"""
		支付宝及时到账交易认证成功逻辑:
			如果认证成功，发送认证成功信号
		"""
		try:
			if self.is_verified:
				raise Exception('%r is verified already' % self)

			self.is_verified = True
			self.save(force_update=True)
			payment_verify_success_signal.send_robust(sender=self.__class__, payment=self)

		except Exception, err:
			logger.critical('%r verify success error:%s' % (self, err))


	def _verify_fail(self, reason, re_verify=True, **kwargs):
		"""
		支付宝及时到账交易认证成功逻辑:
			如果认证成功，发送认证失败信号
		"""		
		payment_verify_fail_signal.send(sender=self.__class__, 
										payment=self,
										reason=reason,
										re_verify=re_verify)


"""
支付宝及时到账交易信号连接
"""

# 连接支付宝及时到账交易认证成功信号
payment_verify_success_signal.connect(order_payment_verify_success_handler, 
					sender=AlipayDirectPay,
					weak=False, 
					dispatch_uid="alipay.signals.directpay_payment_verify_success")
