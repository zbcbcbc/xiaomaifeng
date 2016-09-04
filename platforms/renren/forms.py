# -*- coding: utf-8 -*-

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"




from django import forms

from models import RenrenAlbum

class AddRenrenAlbumForm(forms.ModelForm):

	class Meta:
		model = RenrenAlbum

	def __init__(self, *args, **kwargs):
		super(AddRenrenAlbumForm, self).__init__(*args, **kwargs)
		self.fields['name'].label = u"相册名称"
		self.fields['description'].label = u"相册简介"
		self.fields['cover_image'].label = u"相册封面"
		self.fields['location'].label = u"相册地点"
		self.fields['visible'].label = u"相册隐私"
		self.fields['description'].label = u"相册简介"
