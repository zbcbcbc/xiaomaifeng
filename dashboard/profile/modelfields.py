# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError

"""
国家Model Field
"""

__all__ = ["CountryField", "isValidCountry"]

COUNTRY_CHOICES = [
    ('CHINA', u'中国')
]

COUNTRY_CHOICES.sort(lambda x,y:cmp(slugify(x[1]),slugify(y[1])))
#COUNTRIES.append(('ZZ', _('其他')))

def _isValidCountry(value):
    if not value in [lang[0] for lang in COUNTRY_CHOICES]:
        raise ValidationError, ugettext(u"无效的国家选择")

class CountryField(models.CharField):
    default_validators = [_isValidCountry]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', 'CHINA')
        kwargs.setdefault('max_length', 10)
        kwargs.setdefault('choices', COUNTRY_CHOICES)
        super(CountryField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"



"""
城市Model Field
"""

CITIES = [
        ('SHANGHAI', u'上海'),
        ('SHENZHEN', u'深圳'),
        ('BEIJING', u'北京'),
]

CITIES.sort(lambda x,y:cmp(slugify(x[1]),slugify(y[1])))
#COUNTRIES.append(('ZZ', _('其他')))

def _isValidCity(value):
    if not value in [lang[0] for lang in CITIES]:
        raise ValidationError, ugettext(u"无效的城市选择")

class CityField(models.CharField):
    default_validators = [_isValidCity]
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 10)
        kwargs.setdefault('choices', CITIES)
        super(CityField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"


"""
添加South Rules
"""

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^dashboard\.profile\.modelfields\.CityField"])
    add_introspection_rules([], ["^dashboard\.profile\.modelfields\.CountryField"])
except ImportError:
    pass




