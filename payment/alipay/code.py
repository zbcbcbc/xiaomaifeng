# -*- coding: utf-8 -*-
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


class BankCode:
	BOCB2C = u'中国银行' 
	ICBCB2C = u'中国工商银行' 
	ICBCBTB = u'中国工商银行(B2B)' 
	CMB = u'招商银行' 
	CCB = u'中国建设银行' 
	CCBBTB = u'中国建设银行(B2B)' 
	ABC = u'中国农业银行' 
	ABCBTB = u'中国农业银行(B2B)' 
	SPDB = u'上海浦东发展银行' 
	SPDBB2B = u'上海浦东发展银行(B2B)' 
	CIB = u'兴业银行' 
	GDB = u'广东发展银行' 
	SDB = u'深圳发展银行' 
	CMBC = u'中国民生银行' 
	COMM = u'交通银行' 
	CITIC = u'中信银行' 
	CEBBANK = u'光大银行' 
	NBBANK = u'宁波银行' 
	HZCBB2C = u'杭州银行' 
	SHBANK = u'上海银行' 
	SPABANK = u'平安银行' 
	BJRCB = u'北京农村商业银行' 
	fdb101 = u'富滇银行' 
	PSBC-DEBIT = u'中国邮政储蓄银行'  
	BJBANK = u'北京银行'

class LogisticsType:
	POST = u'平邮'
	EXPRESS = u'其他快递'
	EMS = 'EMS'
	DIRECT = u'无需物流'

class LogisticsPaymentType:
	BUYER_PAY = u'等待上传凭证'
	SELLER_PAY = u'上传完毕,提交审核,等待审核'
	BUYER_PAY_AFTER_RECEIVE = u'审核未通过,需要重新上传'



class TradeStatus:
	"""
	交易状态
	"""
	WAIT_BUYER_PAY = u'等待买家付款'
	WAIT_SELLER_SEND_GOODS = u'买家已付款,等待卖家发货'
	WAIT_BUYER_CONFIRM_GOODS = u'卖家已发货,等待买家确认'
	TRADE_FINISHED = u'交易成功结束'




class RefundStatus:
	"""
	退款状态
	"""
	WAIT_SELLER_AGREE = u'退款协议等待卖家确认中'
	SELLER_REFUSE_BUYER = u'卖家不同意协议,等待买家修改'
	WAIT_BUYER_RETURN_GOODS = u'退款协议达成,等待买家退货'
	WAIT_SELLER_CONFIRM_GOODS = u'等待卖家收货'
	REFUND_SUCCESS = u'退款成功 ' # 全额退款情况:trade_status= TRADE_CLOSED,而 refund_status=REFUND_SUCCESS, 非全额退款情况:trade_status= TRADE_SUCCESS, 而 refund_status=REFUND_SUCCESS
	REFUND_CLOSED = u'退款关闭'



class Action:
	"""
	操作动作枚举
	"""
	CREATE = u'创建交易'
	PAY = u'付款'
	REFUND = u'退款'
	CONFIRM_GOODS = u'确认收获'
	CANCEL_FAST_PAY = u'付款方取消快速支付'
	FP_PAY = u'快速支付付款'
	MODIFY_DELIVER_ADDRESS = u'买家修改收货地址'
	SEND_GOODS = u'发货'
	REFUSE_TRADE = u'拒绝交易'
	MODIFY_TRADE = u'修改交易'
	CLOSE_TRADE = u'关闭交易'
	QUERY_LOGISTICS = u'查看物流状态'



class AccountType:
	"""
	账户类型枚举
	"""
	CORPORATE_ACCOUNT = u'公司'
	PRIVATE_ACCOUNT = u'个人'
	INTERNAL_CORPORATE_ACCOUNT = u'内部'
	TAOBAO_MIDDLE_ACCOUNT = u'支付宝中间账户'

"""
以下是支付宝及时到部分重要账编码列表
"""

class DirectPayPayMethod:
	"""
	支付渠道
	"""
	DIRECTPAY = u'支付宝帐户余额'
	CARTOON = u'卡通'
	BANKPAY = u'网银'
	CASH = u'现金'


class DirectPayRefundStatus:
	"""
	退款状态
	"""
	REFUND_SUCCESS = u'退款成功 ' # 全额退款情况:trade_status= TRADE_CLOSED,而 refund_status=REFUND_SUCCESS, 非全额退款情况:trade_status= TRADE_SUCCESS, 而 refund_status=REFUND_SUCCESS
	REFUND_CLOSED = u'退款关闭'

class DirectPayTradeStatus:
	"""
	交易状态
	"""
	WAIT_BUYER_PAY = u'交易创建,等待买家付款'
	TRADE_CLOSED = u'在指定时间段内未支付时关闭的交易;在交易完成全额退款成功时关闭的交易。'
	TRADE_SUCCESS = u'交易成功,且可对该交易做操作,如:多级分润、退款等'
	TRADE_PENDING = u'等待卖家收款(买家付款后,如果卖家账号被冻结)'
	TRADE_FINISHED = u'交易成功且结束,即不可再做任何操作'




"""
以下是确认物品发货接口编码列表
"""
class SendGoodsConfirmTransportType:
	"""
	物流类型
	"""
	POST = u'平邮'
	EXPRESS = u'其他快递'
	EMS = 'EMS'
	DIRECT = u'无需物流'




