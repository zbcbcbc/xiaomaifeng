# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import datetime, logging

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic.base import RedirectView
from django.contrib import messages

from dashboard.listing.models import DigitalItem
from platforms.alipay.alipay_python import notify_verify
from models import AlipayDirectPay, AlipayPartnerTrade
from signals import *
from payment.views import *


logger = logging.getLogger('xiaomaifeng.payment')




def partnertrade_return_url_handler(request):
	"""
 	支付宝担保交易同步通知

 	(1) 买家在支付成功后会看到一个支付宝提示交易成功的页面,该页面会停留几 秒,然后会自动跳转回商户指定的同步通知页面(参数 return_url)。
	(2) 该页面中获得参数的方式,需要使用 GET 方式获取,如 request.QueryString("out_trade_no")、$_GET['out_trade_no']。
	(3) 该方式仅仅在买家付款完成以后进行自动跳转,因此只会进行一次。
	(4) 该方式不是支付宝主动去调用商户页面,而是支付宝的程序利用页面自动跳
        转的函数,使用户的当前页面自动跳转。
￼￼￼￼￼￼￼￼￼￼￼￼￼￼￼￼支付宝(中国)网络技术有限公司 版权所有| 版本:1.7 第 26 页支付宝纯担保交易接口
	(5) 该方式可在本机而不是只能在服务器上进行调试。
	(6) 返回 URL 只有一分钟的有效期,超过一分钟该链接地址会失效,验证则会失败。
	(7) 设置页面跳转同步通知页面(return_url)的路径时,不要在页面文件的后面
		再加上自定义参数。例如: 错误的写法:http://www.alipay.com/alipay/return_url.php?xx=11 正确的写法:http://www.alipay.com/alipay/return_url.php
	(8) 由于支付宝会对页面跳转同步通知页面(return_url)的域名进行合法有效性 校验,因此设置页面跳转同步通知页面(return_url)的路径时,不要设置成 本机域名,也不能带有特殊字符(如“!”),如:


 	"""
 	print '>> directpay return url handler start...'
 	if notify_verify(request.GET):
 		# 通知验证成功, 并进行数据同样确认
 		# 根据返回内容作出相应动作，一般是用户认证交易返回认证成功或者失败
 		status = AlipayPartnerTrade.alipay_objects.verify_order(reqiest.GET) #WARNING: in development
 		#如果返回数据成功，
 		#STUB
 		if status:
 			return HttpResponse(u'用户认证支付宝担保交易成功！您的物品即将被送出')
 		else:
 			return HttpResponse(u'用户认证支付宝担保交易交易失败，请重新尝试')
 	else:
 		# 通知验证失败
 		raise Http404



@csrf_exempt
def partnertrade_notify_url_handler(request):
	"""
	支付宝担保交易异步通知

		(1) 必须保证服务器异步通知页面(notify_url)上无任何字符,如空格、HTML 标签、开发系统自带抛出的异常提示信息等;
		(2) 支付宝是用 POST 方式发送通知信息,因此该页面中获取参数的方式,如: request.Form("out_trade_no")、$_POST['out_trade_no'];
		(3) 支付宝主动发起通知,该方式才会被启用;
		(4) 只有在支付宝的交易管理中存在该笔交易,且发生了交易状态的改变,支付
			宝才会通过该方式发起服务器通知(即时到账中交易状态为“等待买家付款”
        	的状态默认是不会发送通知的);
		(5) 服务器间的交互,不像页面跳转同步通知可以在页面上显示出来,这种交互
			方式是不可见的;
		(6) 第一次交易状态改变(即时到账中此时交易状态是交易完成)时,不仅页面
        	跳转同步通知页面会启用,而且服务器异步通知页面也会收到支付宝发来的
			处理结果通知;
		(7) 程序执行完后必须打印输出“success”(不包含引号)。如果商户反馈给支
			付宝的字符不是 success 这 7 个字符,支付宝服务器会不断重发通知,直到 超过24小时22分钟。
			一般情况下,25 小时以内完成 8 次通知(通知的间隔频率一般是: 2m,10m,10m,1h,2h,6h,15h);
			支付宝(中国)网络技术有限公司 版权所有| 版本:1.7 第 27 页纯担保交易接口
		(8) 程序执行完成后,该页面不能执行页面跳转。如果执行页面跳转,支付宝会 收不到 success 字符,会被支付宝服务器判定为该页面程序运行出现异常, 而重发处理结果通知;
		(9) cookies、session 等在此页面会失效,即无法获取这些数据;
		(10) 该方式的调试与运行必须在服务器上,即互联网上能访问;
		(11) 该方式的作用主要防止订单丢失,即页面跳转同步通知没有处理订单更新,
				它则去处理;
		(12) 当商户收到服务器异步通知并打印出success时,服务器异步通知参数
			notify_id 才会失效。也就是说在支付宝发送同一条异步通知时(包含商户并 未成功打印出 success 导致支付宝重发数次通知),服务器异步通知参数 notify_id 是不变的。

	"""
	if request.method == 'POST':
		if notify_verify(request.POST):
			# 异步通知验证成功， 更新对应order 数据
			status = AlipayPartnerTrade.alipay_objects.update_order(request.POST)
 			#如果返回数据成功，
 			#STUB
 			if status:
 				return HttpResponse('fail, but in test')
 			else:
 				return HttpResponse('success')
		else:
			# 异步通知验证失败
			pass

	return Http404



def directpay_return_url_handler(request):
	"""
 	支付宝及时到账同步通知
 	"""
 	print '>> directpay return url handler start'
 	if notify_verify(request.GET):
 		# 通知验证成功, 并进行数据同样确认
		status = AlipayDirectPay.alipay_objects.handle_return_url_data(request.POST)
 		if status:
 			return HttpResponse(u'用户认证支付宝及时到账交易成功！您的付款已经送出')
 		else:
 			return HttpResponse(u'用户认证支付宝及时到账交易交易失败，请重新尝试')
 	else:
 		# 通知验证失败
 		pass

 	raise Http404



@csrf_exempt
def directpay_notify_url_handler(request):
	"""
	支付宝及时到账异步通知
	"""
	if request.method == 'POST':
		if notify_verify(request.POST):
			# 异步通知验证成功， 更新对应order 数据
			status = AlipayDirectPay.alipay_objects.handle_notify_url_data(request.POST)
 			if status:
 				return HttpResponse('fail, but in test')
 			else:
 				return HttpResponse('success')
		else:
			# 异步通知验证失败
			pass

	raise Http404
