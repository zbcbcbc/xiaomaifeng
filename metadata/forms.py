# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django import forms
from django.forms import formsets


from dashboard.models import *
from metadata.models import MetaData




class MetaDataForm(forms.Form):

	name = forms.CharField(max_length=128, required=False)
	value = forms.CharField(max_length=128, required=False)



MetaDataFormset = formsets.formset_factory(MetaDataForm, extra=1, max_num=5)



