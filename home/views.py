# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from django.views.generic.base import TemplateView



class HomeView(TemplateView):
	template_name = 'home/index.html'

	def get_context_data(self, **kwargs):
		return super(HomeView, self).get_context_data(**kwargs)


class TermView(TemplateView):
	template_name = 'home/term.html'

	def get_context_data(self, **kwargs):
		return super(TermView, self).get_context_data(**kwargs)

class PrivacyView(TemplateView):
	template_name = 'home/privacy.html'

	def get_context_data(self, **kwargs):
		return super(PrivacyView, self).get_context_data(**kwargs)