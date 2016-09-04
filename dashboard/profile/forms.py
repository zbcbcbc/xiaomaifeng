# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from datetime import date

from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.decorators import login_required
from django.forms.models import inlineformset_factory
from django.contrib.auth.models import User


from localflavor_cn.formfields import *
from models import UserProfile, UserGroup



class UserProfileForm(forms.ModelForm):

    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=100, required=True)
    zip_code = CNPostCodeField(required=True)
    province = forms.CharField(widget=CNProvinceSelect, required=True)
    mobile = CNCellNumberField(required=True)


    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)

        self.fields.keyOrder = [
            'first_name',
            'last_name',
            'email',
            'province',
            'address_1',
            'address_2',
            'zip_code',           
            'mobile',
            'in_foreign']

        self.fields['first_name'].label = u"名"
        self.fields['last_name'].label = u"姓"
        self.fields['email'].label = u"邮箱地址"
        self.fields['in_foreign'].label = u"是否在中国大陆以外地区"
        self.fields['address_1'].label = u"街道地址"
        self.fields['address_2'].label = u"门牌号"
        self.fields['province'].label = u"省"
        self.fields['zip_code'].label = u"邮编"
        self.fields['mobile'].label = u"手机号码"


        instance = getattr(self, 'instance', None)
        if instance:
            self.fields['first_name'].initial = instance.user.first_name
            self.fields['last_name'].initial = instance.user.last_name
            self.fields['email'].initial = instance.user.email
            self.fields['address_1'].initial = instance.address_1
            self.fields['address_2'].initial = instance.address_2
            self.fields['province'].initial = instance.province
            self.fields['zip_code'].initial = instance.zip_code
            self.fields['mobile'].initial = instance.mobile
            self.fields['in_foreign'].initial = instance.in_foreign
            

    def save(self, force_insert=False, force_update=False, commit=True):
        """
        额外保存用户数据
        提醒：如果commit=False, 用户数据同样不会保存
        """
        instance = super(UserProfileForm, self).save(commit=False)
        user = instance.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        instance.zip_code = self.cleaned_data['zip_code']
        instance.mobile = self.cleaned_data['mobile']
        instance.province = self.cleaned_data['province']
        if commit:
           instance.save()
           user.save()
        return instance



    class Meta:
        model = UserProfile
        exclude = ['user', 'zip_code', 'mobile', 'province']
        



class UpgradeUserForm(forms.Form):
    user_group = forms.ModelChoiceField(queryset=UserGroup.objects.all(), label=u'升级类型')
    period = forms.IntegerField(required=True, label=u'有效时间') #以月来计算









