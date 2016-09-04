# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging, datetime, collections
from itertools import chain

from django.contrib import messages
from django.db.models import Q

from models import Order


logger = logging.getLogger('xiaomaifeng.orders')


class PaymentStatMixin(object):

	def get_monthly_payment_stat(self, user, month=None):
		"""
		默认当月数据
		需要optimization
		"""
		month = month or datetime.datetime.now().month # get current timezone aware month

		orders = Order.objects.filter(finish_time__month=month).filter(Q(buyer=user) | Q(seller=user))

		pay_counter = collections.Counter({0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 
				6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0, 16:0, 17:0,
				18:0, 19:0, 20:0, 21:0, 22:0, 23:0, 24:0, 25:0, 26:0, 27:0, 28:0, 
				29:0, 30:0, 31:0})
		receive_counter = collections.Counter({0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 
				6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0, 16:0, 17:0,
				18:0, 19:0, 20:0, 21:0, 22:0, 23:0, 24:0, 25:0, 26:0, 27:0, 28:0, 
				29:0, 30:0, 31:0})

		platform_counter = collections.Counter()
		location_counter = collections.Counter()

		renren_trade_counter = collections.Counter({0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 
				6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0, 16:0, 17:0,
				18:0, 19:0, 20:0, 21:0, 22:0, 23:0, 24:0, 25:0, 26:0, 27:0, 28:0, 
				29:0, 30:0, 31:0})
		weibo_trade_counter = collections.Counter({0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 
				6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0, 16:0, 17:0,
				18:0, 19:0, 20:0, 21:0, 22:0, 23:0, 24:0, 25:0, 26:0, 27:0, 28:0, 
				29:0, 30:0, 31:0})
		douban_trade_counter = collections.Counter({0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 
				6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0, 16:0, 17:0,
				18:0, 19:0, 20:0, 21:0, 22:0, 23:0, 24:0, 25:0, 26:0, 27:0, 28:0, 
				29:0, 30:0, 31:0})


		for order in orders:
			# TODO: loop optimization
			# Social Platform info
			if order.buyer_id == user.id: #WARNING one extra db hit
				pay_counter[order.start_time.day] += float(order.total_fee) #WARNING: no decimal object here
			elif order.seller_id == user.id:
				receive_counter[order.start_time.day] += float(order.total_fee) - float(order.service_charge)

			# platform counter
			platform_counter[order.social_platform.name] += 1
			# Location counter
			location_counter[order.location] += 1

			if order.social_platform.name == 'renren':
				renren_trade_counter[order.start_time.day] += 1
			elif order.social_platform.name == 'weibo':
				weibo_trade_counter[order.start_time.day] += 1
			elif order.social_platform.name == 'douban':
				douban_trade_counter[order.start_time.day] += 1

		#endfor

		location_total = sum(location_counter.values())
		if location_total <= 0:
			location_percentage = dict()
		else:
			location_percentage = dict(location_counter)
			for location in location_percentage.keys():
				location_percentage[location] = location_percentage[location] / location_total * 100


		r = {}
		r['total_pay'] = sum(pay_counter.values())
		r['total_receive'] = sum(receive_counter.values())
		r['location'] = location_percentage
		r['trade'] = dict()
		r['trade']['renren'] = renren_trade_counter.items()
		r['trade']['weibo'] = weibo_trade_counter.items()
		r['trade']['douban'] = douban_trade_counter.items()
		r['trade']['pay'] = pay_counter.items()
		r['trade']['receive'] = receive_counter.items()
		r['trade']['platform'] = dict(platform_counter.items())


		return r 



