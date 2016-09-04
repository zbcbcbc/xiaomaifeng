# -*- coding: utf-8 -*-
'''
Created on 2011-4-21
支付宝接口
@author: Yefe
'''

from config import *
import hashlib

def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if strings_only and isinstance(s, (types.NoneType, int)):
        return s
    if not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                        errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    elif isinstance(s, unicode):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s

# 网关地址
_GATEWAY = 'https://www.alipay.com/cooperate/gateway.do?'


# 对数组排序并除去数组中的空值和签名参数
# 返回数组和链接串
def params_filter(params):
    ks = params.keys()
    ks.sort()
    newparams = {}
    prestr = ''
    for k in ks:
        v = params[k]
        k = smart_str(k, ALIPAY_INPUT_CHARSET)
        if k not in ('sign','sign_type') and v != '':
            newparams[k] = smart_str(v, ALIPAY_INPUT_CHARSET)
            prestr += '%s=%s&' % (k, newparams[k])
    prestr = prestr[:-1]
    return newparams, prestr


# 生成签名结果
def build_mysign(prestr, key, sign_type = 'MD5'):
    if sign_type == 'MD5':
        m = hashlib.md5()
        m.update(prestr + key)
        return m.hexdigest()
    return ''




def notify_verify(post):
    # 初级验证--签名
    _,prestr = params_filter(post)
    mysign = build_mysign(prestr, ALIPAY_KEY, ALIPAY_SIGN_TYPE)
    if mysign != post.get('sign'):
        return False
    
    # 二级验证--查询支付宝服务器此条信息是否有效
    params = {}
    params['partner'] = ALIPAY_PARTNER
    params['notify_id'] = post.get('notify_id')
    if ALIPAY_TRANSPORT == 'https':
        params['service'] = 'notify_verify'
        gateway = 'https://www.alipay.com/cooperate/gateway.do'
    else:
        gateway = 'http://notify.alipay.com/trade/notify_query.do'
    veryfy_result = urlopen(gateway, urlencode(params)).read()
    if veryfy_result.lower().strip() == 'true':
        return True
    return False
"""
以下是新加入
"""






# 标准双接口
def trade_create_by_buyer(tn, subject, body, price):
    """
    标准双接口
    这个接口可能不被启用
    """
    params = {}
    """
    必须填写的基本参数
    """
    params['service']       = 'trade_create_by_buyer' # 接口名称。
    params['partner']           = ALIPAY_PARTNER # 签约的支付宝账号对应的支付宝唯一用户号, 以 2088 开头的 16 位纯数 字组成。
    params['_input_charset']    = ALIPAY_INPUT_CHARSET # 商户网站使用的编码格式, 如 utf-8、gbk、gb2312 等。
    params['notify_url']        = ALIPAY_NOTIFY_URL # 支付宝服务器主动通知商 户网站里指定的页面 http 路径。可空
    params['return_url']        = ALIPAY_RETURN_URL # 支付宝处理完请求后,当前 页面自动跳转到商户网站 里指定页面的 http 路径, 可空

    """
    必须填写的业务参数
    """
    params['out_trade_no']  = tn        # 支付宝合作商户网站唯一 订单号(确保在合作伙伴系 统中唯一)。String(6 4)
    params['subject']       = subject   # 商品的标题/交易标题/订单 标题/订单关键字等。该参数最长为 128 个汉字. String(2 56)
    params['payment_type']  = '1' # 收款类型,只支持 1:商品 购买。
    params['logistics_type'] = 'POST'   # 第一组物流类型。取值范围请参见附录 “11.3 物流类型”。
    params['logistics_fee'] = '0.00' # 第一组物流运费。单位为:RMB Yuan。精确 到小数点后两位。缺省值为 0 元。  
    params['logistics_payment'] = 'BUYER_PAY' # 第一组物流支付类型。取值范围请参见附录 “11.4 物流支付类型”。
    #params['seller_email']      = settings.ALIPAY_SELLER_EMAIL # 登录时,seller_email 和 seller_id 两者必填一个。String(1 00)
    params['price'] = price             # 单位为:RMB Yuan。取值 范围为 [0.01,1000000.00],精确 到小数点后两位。
    params['quantity'] = 1              # 商品的数量
    params['body']          = body      # 对一笔交易的具体描述信 息。如果是多种商品,请将 商品描述字符串累加传给 body。String(4 00), 可空
    params['discount'] = 0 # 单位为:RMB Yuan。取值 范围为 [-100000000.00,1000000 00.00],精确到小数点后两 位。可空
    params['total_fee'] = 0 # 交易金额大于 0 元。担保交易单笔交易金额不 能超过 100 万,精确到小 数点后两位。即时到账无金额上限。选填项。
    params['show_url'] = ALIPAY_SHOW_URL   # 收银台页面上,商品展示的 超链接。可空
    params['seller_id'] = '' # 卖家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数 字。登录时,seller_email 和 seller_id 两者必填一个。可空 String(3 0)
    #params['buyer_email'] = '' # 买家支付宝账号。String(1 00), 可空
    params['buyer_id'] = '' # 买家支付宝账号对应的支付宝唯一用户号。以 2088 开头的纯 16 位数 字。可空
    params['seller_account_name'] = '' # 如果 seller_email 和 seller_id 均为空,则以此别 名账号作为卖家账号。String(1 00) 可空
    params['buyer_account_name'] = '' # 如果 buyer_email 和 buyer_id 均为空,则以此 别名账号作为买家账号。String(1 00) 可空 
    params['receive_name'] = '' # 收货人姓名。String(1 28) 可空
    params['receive_address'] = '' # 收货人地址。String(2 56) 可空
    params['receive_zip'] = '' # 收货人邮编。String(2 0) 可空
    params['receive_phone'] = '' # 收货人电话。 String(3 0)
    params['receive_mobile'] = '' #收货人手机。String 可空
    params['logistics_type_1'] = '' # 第二组物流类型。取值范围请参见附录 “11.3 物流类型”。可空
    params['logistics_fee_1'] = '' # 第二组物流运费。单位为:RMB Yuan。精确 到小数点后两位。可空
    params['logistics_payment_1'] = '' # 第二组物流支付类型。取值范围请参见附录 “11.4 物流支付类型”
    params['logistics_type_2'] = '' # 第三组物流类型。取值范围请参见附录 “11.3 物流类型”。可空
    params['logistics_fee_2'] = '' # 第三组物流运费。单位为:RMB Yuan。精确 到小数点后两位。可空
    params['logistics_payment_2'] = '' # 第三组物流支付类型。取值范围请参见附录 “11.4 物流支付类型”  

    """
    只有开通了自定义超时功能,设置的请求参数 t_s_send_1、t_s_send_2、t_b_rec_post、it_b_pay 才有效。
    """  
    params['it_b_pay'] = '' # 设置未付款交易的超时时 间,一旦超时,该笔交易就 会自动被关闭。取值范围:1m~15d。m-分钟,h-小时,d-天,1c- 当天(无论交易何时创建, 都在 0 点关闭)。该参数数值不接受小数点, 如 1.5h,可转换为 90m。该功能需要联系支付宝配置关闭时间。
    params['t_s_send_1'] = '' # 卖家逾期不发货,允许买家 退款的期限。如果商户未设置支持自定义超时,该参数应该为空,否则会报错。单位为天(d)。
    params['t_s_send_2'] = '' # 卖家逾期不发货,建议买家 退款。如果商户未设置支持自定义超时,该参数应该为空,否则会报错。单位为天(d)。
    params['t_b_rec_post'] = '' # 买家逾期不确认收货,自动 完成交易(平邮)的期限。如果商户未设置支持自定义超时,该参数应该为空,否则会报错。单位为天(d)。
    params['anti_phishing_key'] = '' # 通过时间戳查询接口获取的加密支付宝系统时间戳。如果已申请开通防钓鱼时间戳验证,则此字段必填。

    """
    只有开通了快捷登录,才能使用请求参数 token(授权 令牌码),且必须设置 token。
    """
    params['token'] = '' # 如果开通了快捷登录产品,则需要填写;如果没有开通,则为空。String(4 0)

    params,prestr = params_filter(params)
    params['sign'] = build_mysign(prestr, ALIPAY_KEY, ALIPAY_SIGN_TYPE) # 请参见“8 签名机制”。 
    params['sign_type'] = ALIPAY_SIGN_TYPE# DSA、RSA、MD5 三个值 可选,必须大写。

    return _GATEWAY + urlencode(params)




__all__ = ["smart_str", "params_filter", "build_mysign", "notify_verify"]
