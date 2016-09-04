# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

from decimal import Decimal

from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils import simplejson
from django.utils.safestring import mark_safe
from django.template import Library

register = Library()

@register.filter(is_safe=True)
def jsonify(object):
	if isinstance(object, QuerySet):
		return mark_safe(serialize('json', object))
	return mark_safe(simplejson.dumps(object))

