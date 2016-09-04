# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "rafaelsierra"
__repo__ = "https://github.com/rafaelsierra/django-metadata/"
__editor__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from metadata.models import MetaData
from django.contrib.contenttypes import generic

class MetaDataTabularInline(generic.GenericTabularInline):
    model = MetaData
    
class MetaDataStackedInline(generic.GenericStackedInline):
    model = MetaData