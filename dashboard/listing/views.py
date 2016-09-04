# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


import logging
from itertools import chain

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.template import RequestContext  # For CSRF
from django.http import HttpResponseRedirect, Http404
from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.cache import cache
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.db import IntegrityError, transaction

from platforms.forms import SelectSocialClientForm
from metadata.forms import MetaDataFormset
from metadata.models import MetaData
from platforms.mixin import *
from forms import PaybackFundForm, DonationFundForm, DigitalItemForm, PhysicalItemForm, EventItemForm
from models import DigitalItem, PhysicalItem, PaybackFund, DonationFund, EventItem



logger = logging.getLogger('xiaomaifeng.listing')



ITEM_CALLBACK_URL = 'http://www.chaojijisuzhifu.com/dashboard/itemlist/renew_access_token/'




class ItemListView(ListView):
	template_name = 'listing/itemlist.html'
	context_object_name = 'items'

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ItemListView, self).dispatch(*args, **kwargs)

	def get_queryset(self):
		"""
		TODO: cache
		"""
		digital_items = DigitalItem.objects.filter(user=self.request.user)
		physical_items = PhysicalItem.objects.filter(user=self.request.user)

		item_list = list(chain(digital_items, physical_items))
		return item_list


	def get_context_data(self, **kwargs):
		return super(ItemListView, self).get_context_data(**kwargs)


class EventListView(ListView):
	template_name = 'listing/eventlist.html'
	context_object_name = 'events'

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(EventListView, self).dispatch(*args, **kwargs)

	def get_queryset(self):
		"""
		TODO: cache
		"""
		return EventItem.objects.filter(user=self.request.user)



	def get_context_data(self, **kwargs):
		return super(EventListView, self).get_context_data(**kwargs)



class FundListView(ListView):
	template_name = 'listing/fundlist.html'
	context_object_name = 'funds'

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(FundListView, self).dispatch(*args, **kwargs)

	def get_queryset(self):
		"""
		TODO: cache
		"""
		donation_funds = DonationFund.objects.filter(user=self.request.user)
		payback_funds = PaybackFund.objects.filter(user=self.request.user)
		return list(chain(donation_funds, payback_funds))

	def get_context_data(self, **kwargs):
		return super(FundListView, self).get_context_data(**kwargs)




class CreateMerchandiseView(MerchandiseToSocialClientsMixin, CreateView):
	"""
	This is Abstract Class, Please subclass it for proper use
	添加物品，包括了上传到人人或者新浪微博
	此方法不能直接使用，使用CreatePhysicalItemView 或者 CreateDigitalItemView
	"""

	#client_form_class = SelectSocialClientForm
	

	def get_context_data(self, **kwargs):
		context = super(CreateMerchandiseView, self).get_context_data(**kwargs)
		context['select_client_form'] = SelectSocialClientForm(user=self.request.user)
		context['metadata_formset'] = MetaDataFormset()
		return context


	def post(self, request, **kwargs):
		# get user instance
		form_class = self.get_form_class()
		# 物品表格
		merchandise_form = form_class(request.POST, request.FILES)
		# 物品Metadata表格
		metadata_formset = MetaDataFormset(request.POST)
		# 选择社交帐号表格
		select_client_form = SelectSocialClientForm(request.POST, user=request.user)
		# 认证表格合法性

		if merchandise_form.is_valid() and metadata_formset.is_valid() and select_client_form.is_valid():
			return self.form_valid(merchandise_form, metadata_formset, select_client_form)
		else:
			# one of the form is invalid
			return self.form_invalid(merchandise_form, metadata_formset, select_client_form)

	def form_valid(self, merchandise_form, metadata_formset, client_form):
		merchandise_form.instance.user = self.request.user

		# examine if the user has created more than limit merchandises
		if hasattr(settings, 'MERCHANDISE_LIMIT_PER_TYPE'):
			merchandise_count = merchandise_form.instance.__class__.objects.filter(user=self.request.user).count()
			if merchandise_count > settings.MERCHANDISE_LIMIT_PER_TYPE:
				return self.form_invalid(merchandise_form, metadata_formset, client_form, 
								error_msg=u'用户已经超过物品创建数量上限：%s' % settings.MERCHANDISE_LIMIT_PER_TYPE)
		
		with transaction.commit_manually():
			_CREATE_SUCCESS = False
			try:
				sid = transaction.savepoint()
				#TODO database transaction
				merchandise = merchandise_form.save(commit=True)
				# 添加Meta data to item
				for form in metadata_formset:
					data = form.cleaned_data
					if data:
						name = data['name']
						value = data['value']
						merchandise.metadata[name] = value
				transaction.savepoint_commit(sid)
				_CREATE_SUCCESS = True
			except IntegrityError, err:
				# 物品保存错误，返回
				logger.critical(u"%r err:%s" % (self, err))
				transaction.savepoint_rollback(sid)
			finally:
				transaction.commit()
				if not _CREATE_SUCCESS:
					return self.form_invalid(merchandise_form, metadata_formset, client_form, error_msg=u'物品创建失败')
			

		messages.success(self.request, u'添加成功', extra_tags=getattr(self, 'msg_tags', None))
		logger.info(u"%r create %r success" % (self, merchandise))
		
		# 添加物品到用户选择的社交帐户
		self.upload_to_social_clients(request=self.request, merchandise=merchandise, client_form=client_form)

		# 返回物品列表页面

		self.object = merchandise
		return HttpResponseRedirect(self.get_success_url())

		

	def form_invalid(self, merchandise_form, metadata_formset, client_form, error_msg=None):
		#import pprint
		#pprint.pprint(vars(metadata_formset))
		messages.warning(self.request, error_msg or u'添加失败', extra_tags=getattr(self, 'msg_tags', None))
		logger.info(u"%r:%r" % (self, u'%r fill form error' % (self.request.user)))

		ctx = {'form':merchandise_form, 
				'select_client_form':client_form, 
				'metadata_formset': metadata_formset}
		
		return render(self.request, self.template, ctx)	




class CreateDigitalItemView(CreateMerchandiseView):

	form_class = DigitalItemForm
	#client_form_class = SelectSocialClientForm
	model = DigitalItem
	context_object_name = "item"
	template_name = 'listing/addItem_digital.html'
	success_url = reverse_lazy('dashboard:listing:itemlist')

	@method_decorator(login_required)
	#@method_decorator(permission_required('alipay.can_post', login_url=success_url))
	def dispatch(self, *args, **kwargs):
		"""
		template, msg_tags, TAG 为必须添加
		"""
		self.template = 'listing/addItem_digital.html'
		self.msg_tags = 'item-list, add-item'

		return super(CreateDigitalItemView, self).dispatch(*args, **kwargs)
		



class CreatePhysicalItemView(CreateMerchandiseView):

	form_class = PhysicalItemForm
	#client_form_class = SelectSocialClientForm
	model = PhysicalItem
	context_object_name = "item"
	template_name = 'listing/addItem_physical.html'
	success_url = reverse_lazy('dashboard:listing:itemlist')

	@method_decorator(login_required)
	#@method_decorator(permission_required('alipay.can_post', login_url=success_url))
	def dispatch(self, *args, **kwargs):
		self.template = 'listing/addItem_physical.html'
		self.msg_tags = 'item-list, add-item'
		return super(CreatePhysicalItemView, self).dispatch(*args, **kwargs)


class CreateEventItemView(CreateMerchandiseView):

	form_class = EventItemForm
	#client_form_class = SelectSocialClientForm
	model = EventItem
	context_object_name = "item"
	template_name = 'listing/addItem_event.html'
	success_url = reverse_lazy('dashboard:listing:eventlist')

	@method_decorator(login_required)
	#@method_decorator(permission_required('alipay.can_post', login_url=success_url))
	def dispatch(self, *args, **kwargs):
		self.template = 'listing/addItem_event.html'
		self.msg_tags = 'item-list, add-item'
		return super(CreateEventItemView, self).dispatch(*args, **kwargs)



class CreatePaybackFundView(CreateMerchandiseView):

	form_class = PaybackFundForm
	model = PaybackFund
	context_object_name = "fund"
	template_name = "listing/addFund_payback.html"
	success_url = reverse_lazy('dashboard:listing:fundlist')

	@method_decorator(login_required)
	#@method_decorator(permission_required('alipay.can_post', login_url=success_url))
	def dispatch(self, *args, **kwargs):
		self.template = 'listing/addFund_payback.html'
		self.msg_tags = 'fund-list, add-fund'
		return super(CreatePaybackFundView, self).dispatch(*args, **kwargs)


class CreateDonationFundView(CreateMerchandiseView):

	form_class = DonationFundForm
	#client_form_class = SelectSocialClientForm
	model = DonationFund
	context_object_name = "fund"
	template_name = 'listing/addFund_donation.html'
	success_url = reverse_lazy('dashboard:listing:fundlist')

	@method_decorator(login_required)
	#@method_decorator(permission_required('alipay.can_post', login_url=success_url))
	def dispatch(self, *args, **kwargs):
		self.template = 'listing/addFund_donation.html'
		self.msg_tags = 'fund-list, add-fund'
		return super(CreateDonationFundView, self).dispatch(*args, **kwargs)






class UpdateMerchandiseView(MerchandiseToSocialClientsMixin, UpdateView):
	"""
	更新物品，包括了上传到人人或者新浪微博
	这个方法不能使用，请使用Subclass子方法
	"""

	def get_object(self, requeryset=None):
		return super(UpdateMerchandiseView, self).get_object()


	def get_context_data(self, **kwargs):
		context = super(UpdateMerchandiseView, self).get_context_data(**kwargs)
		
		"""
		缓存物品的post数据，每个间隔刷新一次缓存
		"""
		cache_key = 'dashboard.listing.item-detail.cache_key'
		cache_time = 10 # time to live in seconds, in debug mode this is very short

		merchandise = self.get_object()

		merchandise_posts = cache.get(cache_key)
		if not merchandise_posts:
			# 更新缓存			
			merchandise_posts = self.update_merchandise_posts(merchandise)
			cache.set(cache_key, merchandise_posts, cache_time)
		context['content_posts'] = merchandise_posts
		# 获取物品metadata
		metadatas = MetaData.objects.get_content_metadata(merchandise)
		initial = []
		for metadata in metadatas:
			initial.append({'name':metadata.name, 'value':metadata.value})

		context['metadata_formset'] = MetaDataFormset(initial=initial)
		# 物品连接社交网络表格
		context['select_client_form'] = SelectSocialClientForm(self.request.POST, user=self.request.user, content=merchandise)

		return context


	def post(self, request, **kwargs):
		# get content instance
		self.object = self.get_object()

		merchandise_form_class = self.get_form_class()
		merchandise_form = self.get_form(merchandise_form_class)
		# 物品Metadata表格
		metadata_formset = MetaDataFormset(request.POST)

		select_client_form = SelectSocialClientForm(request.POST, user=request.user)

		if merchandise_form.is_valid() and metadata_formset.is_valid() and select_client_form.is_valid():
			return self.form_valid(merchandise_form, metadata_formset, select_client_form)
		else:
			# one of the form is invalid
			return self.form_invalid(merchandise_form, metadata_formset, select_client_form)


	@transaction.commit_on_success
	def form_valid(self, merchandise_form, metadata_formset, client_form):
		try:
			merchandise = merchandise_form.save(commit=True)
			# 保存物品metadata
			for form in metadata_formset:
				data = form.cleaned_data
				if data:
					name = data['name']
					value = data['value']
					merchandise.metadata[name] = value

		except IntegrityError, err:
			# 物品保存错误，返回
			logger.critical(u"%r err: %s" % (self, err))
			return self.form_invalid(merchandise_form, metadata_formset, client_form, error_msg=u'请重新填写物品信息')

		messages.success(self.request, u'更新成功', extra_tags=getattr(self, 'msg_tags', None))
		logger.info(u"%r update %r success" % (self, merchandise))
		
		# 添加物品到用户选择的社交帐户
		self.upload_to_social_clients(request=self.request, merchandise=merchandise, client_form=client_form)

		# 返回物品列表页面
		return HttpResponseRedirect(self.get_success_url())


	def form_invalid(self, merchandise_form, metadata_formset, client_form):
		
		messages.warning(self.request, u'物品失败', extra_tags=getattr(self, 'msg_tags', None))
		logger.info(u"%s:%s" % (self.__class__, u'用户%s表格填写错误' % (self.request.user)))

		ctx = {'form':merchandise_form, 
				'select_client_form':client_form, 
				'item':self.object, 
				'metadata_formset': metadata_formset}

		return render(self.request, self.template, ctx)



class UpdatePhysicalItemView(UpdateMerchandiseView):
	form_class = PhysicalItemForm
	#client_form_class = SelectSocialClientForm
	model = PhysicalItem
	context_object_name = "item"
	template_name = 'listing/updateItem_physical.html'
	success_url = reverse_lazy('dashboard:listing:itemlist')

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		self.template = 'listing/updateItem_physical.html'
		self.msg_tags = 'update-item'
		return super(UpdatePhysicalItemView, self).dispatch(*args, **kwargs)


class UpdateDigitalItemView(UpdateMerchandiseView):
	form_class = DigitalItemForm
	#client_form_class = SelectSocialClientForm
	model = DigitalItem
	context_object_name = "item"
	template_name = 'listing/updateItem_digital.html'
	success_url = reverse_lazy('dashboard:listing:itemlist')

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		self.template = 'listing/updateItem_digital.html'
		self.msg_tags = 'update-item'
		return super(UpdateDigitalItemView, self).dispatch(*args, **kwargs)



class UpdateEventItemView(UpdateMerchandiseView):
	form_class = EventItemForm
	#client_form_class = SelectSocialClientForm
	model = EventItem
	context_object_name = "item"
	template_name = 'listing/updateItem_event.html'
	success_url = reverse_lazy('dashboard:listing:itemlist')

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		self.template = 'listing/updateItem_event.html'
		self.msg_tags = 'update-item'
		return super(UpdateEventItemView, self).dispatch(*args, **kwargs)


class EventItemAttendersView(ListView):
	template_name = 'listing/eventattenders.html'
	context_object_name = 'attenders'

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(EventItemAttendersView, self).dispatch(*args, **kwargs)

	def get_queryset(self):
		"""
		TODO: cache
		"""
		event_item = get_object_or_404(EventItem, user=self.request.user, pk=self.args[1])
		return event_item.get_event_attenders()


	def get_context_data(self, **kwargs):
		return super(EventItemAttendersView, self).get_context_data(**kwargs)




class UpdateDonationFundView(UpdateMerchandiseView):
	"""
	更新筹资，包括了上传到人人或者新浪微博
	"""

	form_class = DonationFundForm
	#client_form_class = SelectSocialClientForm
	model = DonationFund
	context_object_name = "fund"
	template_name = 'listing/updateFund_donation.html'
	success_url = reverse_lazy('dashboard:listing:fundlist')

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		self.template = 'listing/updateFund_donation.html'
		self.msg_tags = 'update-fund'
		return super(UpdateDonationFundView, self).dispatch(*args, **kwargs)


class UpdatePaybackFundView(UpdateMerchandiseView):
	"""
	更新筹资，包括了上传到人人或者新浪微博
	"""

	form_class = PaybackFundForm
	#client_form_class = SelectSocialClientForm
	model = PaybackFund
	context_object_name = "fund"
	template_name = 'listing/updateFund_payback.html'
	success_url = reverse_lazy('dashboard:listing:fundlist')

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		self.template = 'listing/updateFund_payback.html'
		self.msg_tags = 'update-fund'
		return super(UpdatePaybackFundView, self).dispatch(*args, **kwargs)




class DigitalItemView(DetailView):
	model = DigitalItem
	template_name = 'listing/item_detail.html'
	context_object_name = 'item'

	def dispatch(self, *args, **kwargs):
		return super(DigitalItemView, self).dispatch(*args, **kwargs)


	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		context = super(DigitalItemView, self).get_context_data(**kwargs)
		return context


class PhysicalItemView(DetailView):
	model = PhysicalItem
	template_name = 'listing/item_detail.html'
	context_object_name = 'item'

	def dispatch(self, *args, **kwargs):
		return super(PhysicalItemView, self).dispatch(*args, **kwargs)


	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		context = super(PhysicalItemView, self).get_context_data(**kwargs)
		return context


class EventItemView(DetailView):
	model = EventItem
	template_name = 'listing/item_detail.html'
	context_object_name = 'item'

	def dispatch(self, *args, **kwargs):
		return super(EventItemView, self).dispatch(*args, **kwargs)


	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		context = super(EventItemView, self).get_context_data(**kwargs)
		return context


class DonationFundView(DetailView):
	"""
	筹资详细页面，不用用户登陆，用户不可以对筹资作出动作
	"""
	model = DonationFund
	template_name = 'listing/fund_detail.html'
	context_object_name = 'fund'


	def dispatch(self, *args, **kwargs):
		return super(DonationFundView, self).dispatch(*args, **kwargs)


	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		context = super(DonationFundView, self).get_context_data(**kwargs)
		return context


class PaybackFundView(DetailView):
	"""
	筹资详细页面，不用用户登陆，用户不可以对筹资作出动作
	"""
	model = PaybackFund
	template_name = 'listing/fund_detail.html'
	context_object_name = 'fund'


	def dispatch(self, *args, **kwargs):
		return super(PaybackFundView, self).dispatch(*args, **kwargs)


	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		context = super(PaybackFundView, self).get_context_data(**kwargs)
		return context



class DeleteDigitalItemView(DeleteView):
	model = DigitalItem
	success_url = reverse_lazy('dashboard:listing:itemlist')


class DeletePhysicalItemView(DeleteView):
	model = PhysicalItem
	success_url = reverse_lazy('dashboard:listing:itemlist')	


class DeleteEventItemView(DeleteView):
	model = EventItem
	success_url = reverse_lazy('dashboard:listing:eventlist')	


class DeleteDonationFundView(DeleteView):
	model = DonationFund
	success_url = reverse_lazy('dashboard:listing:fundlist')


class DeletePaybackFundView(DeleteView):
	model = PaybackFund
	success_url = reverse_lazy('dashboard:listing:fundlist')





