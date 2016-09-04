# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from django import forms


class AlipayConfrimShippingForm(forms.Form):
	logistics_name = forms.CharField(max_length=64, required=True)
	invoice_no = forms.CharField(max_length=32, required=False)
	transport_type = forms.CharField(max_length=50, required=False)
	seller_ip = forms.CharField(max_length=15, required=False)