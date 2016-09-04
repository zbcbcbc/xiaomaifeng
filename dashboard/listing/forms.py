# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



import logging, pytz

from django.db.models.fields.files import FieldFile
from django.core.exceptions import ValidationError
from django.utils import timezone as djtimezone
from django import forms
from django.contrib.auth.models import User
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from siteutils.datetimewidget import DateTimeWidget
from models import DigitalItem, PhysicalItem, PaybackFund, DonationFund, EventItem
from widgets import AdminImageWidget
			

logger = logging.getLogger('xiaomaifeng.listing')


class ContentForm(forms.models.ModelForm):

	class Meta:
		exclude = ['user', 'add_date']



class PhysicalItemForm(ContentForm):

	# the use of adminimage widget is to be determined
	# under development
		
	def __init__(self, *args, **kwargs):
		super(PhysicalItemForm, self).__init__(*args, **kwargs)
		
		self.fields.keyOrder = [
			'name',
			'description',
			'price',
			'availability',
			'purchase_limit',
			'image',
			'logistics_type',
			'logistics_fee',
			'logistics_payment']
		
		self.fields['name'].label = u"物品名称"
		self.fields['description'].label = u"物品简介"
		self.fields['availability'].label = u"货存" 		
		self.fields['price'].label = u"物品价格"
		self.fields['purchase_limit'].label = u"用户限购数量"
		self.fields['image'].label = u"物品照片"
		self.fields['logistics_type'].label = u"物流类型"
		self.fields['logistics_fee'].label = u"物流价格"
		self.fields['logistics_payment'].label = u"物流支付方式"

		instance = getattr(self, 'instance', None)
		if instance:
			self.fields['name'].initial = instance.name
			self.fields['availability'].initial = instance.availability
			self.fields['purchase_limit'].initial = instance.purchase_limit
			self.fields['price'].initial = instance.price
			self.fields['description'].inital = instance.description
			self.fields['image'].initial = instance.image
			self.fields['logistics_type'].initial = instance.logistics_type
			self.fields['logistics_fee'].initial = instance.logistics_fee
			self.fields['logistics_payment'].initial = instance.logistics_payment


	class Meta(ContentForm.Meta):
		model = PhysicalItem
		widgets = {
			'image': AdminImageWidget(),
		}
		


class DigitalItemForm(ContentForm):

	# the use of adminimage widget is to be determined
	# under development
	def __init__(self, *args, **kwargs):
		super(DigitalItemForm, self).__init__(*args, **kwargs)

		self.fields.keyOrder = [
			'name',
			'description',
			'price',
			'availability',
			'purchase_limit',
			'image',
			'digital_file']

		self.fields['name'].label = u"物品名称"
		self.fields['availability'].label = u"货存"
		self.fields['purchase_limit'].label = u"用户限购数量"
		self.fields['price'].label = u"物品价格"
		self.fields['image'].label = u"物品照片"
		self.fields['description'].label = u"物品简介"
		self.fields['digital_file'].label = u"虚拟物品文件"


		instance = getattr(self, 'instance', None)
		if instance:
			self.fields['name'].initial = instance.name
			self.fields['availability'].initial = instance.availability
			self.fields['price'].initial = instance.price
			self.fields['purchase_limit'].initial = instance.purchase_limit
			self.fields['image'].initial = instance.image
			self.fields['description'].inital = instance.description
			self.fields['digital_file'].initial = instance.digital_file


	class Meta(ContentForm.Meta):
		model = DigitalItem
		widgets = {
			'image': AdminImageWidget(),
		}


class EventItemForm(ContentForm):

	def __init__(self, *args, **kwargs):
		super(EventItemForm, self).__init__(*args, **kwargs)

		self.fields.keyOrder = [
			'name',
			'description',
			'price',
			'availability',
			'purchase_limit',
			'image',
			'event_start']

		self.fields['name'].label = u"活动名称"
		self.fields['availability'].label = u"门票数量"
		self.fields['purchase_limit'].label = u"用户限购数量"
		self.fields['price'].label = u"活动门票价格"
		self.fields['image'].label = u"活动照片"
		self.fields['description'].label = u"活动简介"
		self.fields['event_start'].label = u"活动开始时间"
		



		instance = getattr(self, 'instance', None)
		if instance:
			self.fields['name'].initial = instance.name
			self.fields['availability'].initial = instance.availability
			self.fields['price'].initial = instance.price
			self.fields['purchase_limit'].initial = instance.purchase_limit
			self.fields['description'].inital = instance.description
			self.fields['image'].initial = instance.image
			self.fields['event_start'].initial = instance.event_start



	
	def clean_event_start(self):
		event_start = self.cleaned_data['event_start']

		if not djtimezone.is_aware(event_start):
			raise ValidationError(u"必须填写时区日期")

		event_start_tz = event_start.tzinfo

		_now = djtimezone.now().astimezone(event_start_tz)

		# 注意timezone unawareness
		if _now > event_start:
			raise ValidationError(_(u"活动开始日期不能早与目前时间"))
		return event_start
	



	class Meta(ContentForm.Meta):
		model = EventItem
		widgets = {
			'event_start': DateTimeWidget(),
			'expire_date': DateTimeWidget(),
			'image': AdminImageWidget(),
		}
		exclude = ['time_zone',]


class PaybackFundForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(PaybackFundForm, self).__init__(*args, **kwargs)

		self.fields.keyOrder = [
			'name',
			'description',
			'price',
			'goal',
			'image']


		self.fields['name'].label = u"筹资名称"
		self.fields['image'].label = u"筹资照片"
		self.fields['price'].label = u"单比价格"
		self.fields['goal'].label = u"筹资目标"
		self.fields['description'].label = u"筹资简介"


		instance = getattr(self, 'instance', None)
		if instance:
			self.fields['name'].initial = instance.name
			self.fields['image'].inital = instance.image
			self.fields['price'].initial = instance.price
			self.fields['goal'].initial = instance.goal
			self.fields['description'].initial = instance.description

	class Meta:
		model = PaybackFund
		widgets = {
			'image': AdminImageWidget(),
		}
		exclude = ['user', 'raised', 'add_date']
	


class DonationFundForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(DonationFundForm, self).__init__(*args, **kwargs)

		self.fields.keyOrder = [
			'name',
			'description',
			'price',
			'goal',
			'image']

		self.fields['name'].label = u"筹资名称"
		self.fields['image'].label = u"筹资照片"
		self.fields['price'].label = u"单比价格"
		self.fields['goal'].label = u"筹资目标"
		self.fields['description'].label = u"筹资简介"

		instance = getattr(self, 'instance', None)
		if instance:
			self.fields['name'].initial = instance.name
			self.fields['image'].inital = instance.image
			self.fields['price'].initial = instance.price
			self.fields['goal'].initial = instance.goal
			self.fields['description'].initial = instance.description
			

	class Meta:
		model = DonationFund
		widgets = {
			'image': AdminImageWidget(),
		}
		exclude = ['raised']






