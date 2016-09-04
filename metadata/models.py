# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "rafaelsierra"
__repo__ = "https://github.com/rafaelsierra/django-metadata/"
__editor__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


import json


from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType




class MetaDataManagerBase(models.Manager):
    '''This manager allow to with MetaData.objects as a Dict (useful for
    templates).'''
    def __getitem__(self, key):
        '''Return the value of metadata or None if not found'''
        try:
            return self.get_query_set().get(name=key).value
        except MetaData.DoesNotExist, e:
            return None

    def __setitem__(self, key, value):
        try:
            metadata = self.instance.metadata.get(name=key)
            metadata.value = value
            metadata.save()
        except MetaData.DoesNotExist, e:
            metadata = self.instance.metadata.create(name=key, value=value)

    def __contains__(self, key):
        try:
            if not self[key] is None:
                return True
            else:
                return False
        except IndexError,e:
            return False
        
    def __iter__(self):
        return self.iteritems()


    def iterkeys(self):
        for metadata in self.get_query_set().order_by('name'):
            yield metadata.name

    def keys(self):
        return list(self.iterkeys())

    def itervalues(self):
        # This way we can zip iterkeys and itervalues and retrieve the correct
        # information
        for metadata in self.get_query_set().order_by('name'):
            yield metadata.value

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        for metadata in self.get_query_set().order_by('name'):
            yield metadata.name, metadata.value

    def items(self):
        return list(self.iteritems())





class MetaDataManager(MetaDataManagerBase):
    """
    新添加manager
    """

    def get_content_metadata(self, content):
        content_type = ContentType.objects.get_for_model(content)
        return self.filter(content_type__pk=content_type.id, object_id=content.id)



class MetaData(models.Model):
    name = models.CharField(max_length=128, db_index=True)
    value = models.CharField(max_length=128, db_index=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    objects = MetaDataManager()
    def as_tuple(self):
        '''Return a tuple in the format (name, value)'''
        return (self.name, self.value)
        
    def __repr__(self):
        return json.dumps(dict(
            name=self.name,
            value=self.value,
            content_type=self.content_type.name,
            object_id=self.object_id,
        ))

