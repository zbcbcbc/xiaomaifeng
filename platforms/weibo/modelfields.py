#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator




class WeiboCommentField(models.CharField):
	
	description = "微博评论Field, String(280), 内容不超过140个汉字"

	def __init__(self, *args, **kwargs):
		kwargs.setdefault('max_length', 280)
		super(WeiboCommentField, self).__init__(*args, **kwargs)

	def get_internal_type(self):
		return "CharField"