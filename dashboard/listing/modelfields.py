# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__editor__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"
__author__ = "jespino "
__repo__ = "https://github.com/kaleidos/django-validated-file"

import os.path, uuid, logging
import magic

from django import forms
from django.db import models
from django.template.defaultfilters import filesizeformat
from django.core.files.storage import default_storage
from django.utils.translation import ugettext_lazy as _, ugettext
from django.conf import settings


logger = logging.getLogger('xiaomaifeng.listing')


if hasattr(settings, "AWS_SECRET_ACCESS_KEY"):
    try:
        from backends.S3Storage import S3Storage
        storage = S3Storage()
    except ImportError:
        raise S3BackendNotFound
else:
    storage = default_storage


"""
与物品关联的虚拟文件Field
"""

class DigitalItemFileField(models.FileField):
    def __init__(self, *args, **kwargs):
        self.content_types = kwargs.pop("content_types", [])
        self.max_upload_size = kwargs.pop("max_upload_size", 0)
        self.mime_lookup_length = kwargs.pop("mime_lookup_length", 4096)
        super(DigitalItemFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(DigitalItemFileField, self).clean(*args, **kwargs)

        #if not storage.exists(data.path):
        #    raise forms.ValidationError(_(u"虚拟文件不存在, 请重新上传."))
        try:
            digital_file = data.file
        except IOError, err:
            raise forms.ValidationError(_(u"虚拟文件不存在, 请重新上传."))
            
        if self.content_types:
            uploaded_content_type = getattr(digital_file, 'content_type', '')

            mg = magic.Magic(mime=True)
            content_type_magic = mg.from_buffer(
                digital_file.read(self.mime_lookup_length)
            )
            digital_file.seek(0)

            # Prefere mime-type instead mime-type from http header
            if uploaded_content_type != content_type_magic:
                uploaded_content_type = content_type_magic

            if not uploaded_content_type in self.content_types:
                raise forms.ValidationError(
                    _(u"文件格式 %(type)s 不支持.") % {'type': content_type_magic}
                )

        if self.max_upload_size and hasattr(digital_file, '_size'):
            if digital_file._size > self.max_upload_size:
                raise forms.ValidationError(
                    _(u"不能上传大于 %(max_size)s 的文件. 您的文件大小为 %(current_size)s") %
                    {'max_size': filesizeformat(self.max_upload_size), 'current_size': filesizeformat(digital_file._size)}
                )

        return data


class FileQuota(object):

    def __init__(self, max_usage=-1):
        self.current_usage = 0
        self.max_usage = max_usage

    def update(self, items, attr_name):
        self.current_usage = 0
        for item in items:
            the_file = getattr(item, attr_name, None)
            if the_file:
                try:
                    self.current_usage += the_file.size
                except AttributeError:
                    pass  # Protect against the inconsistence of that the file
                          # has been deleted in storage but still is in the field

    def exceeds(self, size=0):
        if self.max_usage >= 0:
            return (self.current_usage + size > self.max_usage)
        else:
            return False

    def near_limit(self, limit_threshold=0.8):
        return (float(self.current_usage) / float(self.max_usage)) > limit_threshold


class QuotaValidator(object):

    def __init__(self, max_usage):
        self.quota = FileQuota(max_usage)

    def update_quota(self, items, attr_name):
        self.quota.update(items, attr_name)

    def __call__(self, file):
        file_size = file.size
        if self.quota.exceeds(file_size):
            raise forms.ValidationError(
                _('Please keep the total uploaded files under %(total_size)s. With this file, the total would be %(exceed_size)s.' %
                {'total_size': filesizeformat(self.quota.max_usage), 'exceed_size': filesizeformat(self.quota.current_usage + file_size)})
            )



"""
添加South Rules
"""

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^dashboard\.profile\.modelfields\.DigitalItemFileField"])
except ImportError:
    pass
