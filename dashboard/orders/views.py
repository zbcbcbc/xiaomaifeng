# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging
from itertools import chain

from django.utils import timezone as djtimezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.base import RedirectView, TemplateView
from django.shortcuts import get_object_or_404
from django.http import Http404


from models import Order
from payment.alipay.models import AlipayDirectPay, AlipayPartnerTrade
from payment.alipay.forms import AlipayConfrimShippingForm
from metadata.models import MetaData


logger = logging.getLogger('xiaomaifeng.orders')


class OrderListView(ListView):
	template_name = 'orders/orderlist.html'
	context_object_name = 'orders'

	http_method_names = ['get', 'post', 'head', 'options', 'trace']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(OrderListView, self).dispatch(*args, **kwargs)



class SellOrderListView(OrderListView):
	"""
	展示卖出物品列表，包括虚拟物品和实体物品，直接交易或者筹资,必须是经过买家认证过的交易
	Cache queryset, or View
	"""

	def get_queryset(self):
		"""
		#TODO: use QuerySet.values() and values_list()
		"""
		return Order.objects.get_sell_orders(self.request.user)

	def get_context_data(self, **kwargs):
		context = super(SellOrderListView, self).get_context_data(**kwargs)
		context['ordertype'] = u'卖出'
		return context


class BuyOrderListView(OrderListView):
	"""
	展示买入物品列表，包括虚拟物品和实体物品，直接交易或者筹资
	"""

	def get_queryset(self):
		return Order.objects.get_buy_orders(self.request.user)

	def get_context_data(self, **kwargs):
		context = super(BuyOrderListView, self).get_context_data(**kwargs)
		context['ordertype'] = u'买入'
		return context


class OrderDetailView(DetailView):
	model = Order
	template_name = 'orders/order_detail.html'
	context_object_name = 'order'

	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		context = super(OrderDetailView, self).get_context_data(**kwargs)
		# Extra contexts are added here to allow user actions upon orders
		order = context['order']
		if order.is_buyer(self.request.user):
			context['role'] = 'buyer'
		elif order.is_seller(self.request.user):
			context['role'] = 'seller'

		context['payment'] = order.payment_object
		context['merchandise'] = order.merchandise_object
		context['metadatas'] = MetaData.objects.get_content_metadata(order.merchandise_object)

		return context


class VerifyOrderView(RedirectView):
	permanent = False # used for testing, change to True for production

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(VerifyOrderView, self).dispatch(*args, **kwargs)

	def get_redirect_url(self, **kwargs):
		
		pk = kwargs.pop('pk', None)

		if not pk:
			raise Http404

		try:
			order = Order.objects.get(pk=pk)
			if order.payment_verified:
				logger.warning('%r has been verified...' % order)
				raise Http404 #TODO
			elif order.is_expired:
				logger.warning('%r has expired...' % order)
				raise Http404 #TODO

			payment_verify_url = order.get_payment_verify_url()

			#Here is the hack:
			order.payment_object._verify_success()
			
			return payment_verify_url

		except Order.DoesNotExist:
			logger.warning('Order(%s) does not exist...' % pk)
			raise Http404
		except Exception, err:
			logger.critical('verify order view err:%s' % err)
			raise Http404



class BuyerCancelOrderView(TemplateView):
	"""
	用户取消交易页面，只有在交易未认证情况下才可以取消交易
	"""

	template_name = "orders/order_cancel.html"
	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(BuyerCancelOrderView, self).dispatch(*args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(BuyerCancelOrderView, self).get_context_data(**kwargs)
		pk = context.pop('pk', None)
		if not pk:
			raise Http404

		order = get_object_or_404(Order, pk=pk)
		status = order.cancel_by_buyer(self.request.user)
		context['status'] = status
		return context



class SellerCancelOrderView(TemplateView):
	"""
	用户取消交易页面，只有在交易未认证情况下才可以取消交易
	"""

	template_name = "orders/order_cancel.html"
	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(SellerCancelOrderView, self).dispatch(*args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(SellerCancelOrderView, self).get_context_data(**kwargs)
		pk = context.pop('pk', None)
		if not pk:
			raise Http404

		order = get_object_or_404(Order, pk=pk)
		status = order.cancel_by_seller(self.request.user)
		context['status'] = status
		return context





