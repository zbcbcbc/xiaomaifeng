# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


import logging, re
from itertools import chain

from django.utils.encoding import smart_str
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.views.generic.base import View

from models import TicketPass, DigitalFilePass

logger = logging.getLogger('xiaomaifeng.passbook')


SHA1_RE = re.compile('^[a-f0-9]{40}$')



class TicketPassListView(ListView):
	"""
	用户查看自己所拥有的门票二维码
	"""
	model = TicketPass
	template_name = 'passbook/ticketlist.html'
	context_object_name = 'ticketpasss'
	
	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(TicketPassListView, self).dispatch(*args, **kwargs)


	def get_queryset(self):
		"""
		TODO: cache
		"""
		return TicketPass.objects.filter(owner=self.request.user)

	def get_context_data(self, **kwargs):
		return super(TicketPassListView, self).get_context_data(**kwargs)


class DigitalFilePassListView(ListView):
	"""
	用户查看自己所拥有的门票二维码
	"""
	model = DigitalFilePass
	template_name = 'passbook/digitalfilelist.html'
	context_object_name = 'digitalfilepasss'
	
	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DigitalFilePassListView, self).dispatch(*args, **kwargs)


	def get_queryset(self):
		"""
		TODO: cache
		"""
		return DigitalFilePass.objects.filter(owner=self.request.user)

	def get_context_data(self, **kwargs):
		return super(DigitalFilePassListView, self).get_context_data(**kwargs)




class TicketPassDetailView(DetailView):
	model = TicketPass
	template_name = 'passbook/ticketpass_detail.html'
	context_object_name = 'ticketpass'


	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(TicketPassDetailView, self).dispatch(*args, **kwargs)


	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		context = super(TicketPassDetailView, self).get_context_data(**kwargs)
		return context



class DigitalFilePassDetailView(DetailView):
	model = DigitalFilePass
	template_name = 'passbook/digitalfilepass_detail.html'
	context_object_name = 'digitalfilepass'


	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DigitalFilePassDetailView, self).dispatch(*args, **kwargs)


	def get_context_data(self, **kwargs):
		"""
		在这里添加额外的context数据
		"""
		context = super(DigitalFilePassDetailView, self).get_context_data(**kwargs)
		return context



class DigitalFileOutputView(View):

	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DigitalFileOutputView, self).dispatch(*args, **kwargs)


	def get(self, request, *args, **kwargs):
		access_key = kwargs.get('access_key', None)
		if not access_key or not SHA1_RE.search(access_key):
			raise Http404
		try:
			digitalfilepass = DigitalFilePass.objects.get(owner=request.user, access_key__exact=access_key)
			digital_file = open(digitalfilepass.get_file_path(), 'r') #TODO: avoid direct media directory access
			response = HttpResponse(digital_file, mimetype='application/pdf')
			response['Content-Disposition'] = 'attachment; filename=%s.pdf' % (smart_str(digitalfilepass.title))
			return response
		except DigitalFilePass.DoesNotExist:
			return HttpResponse(u"虚拟物品不存在")
		except Exception, err:
			logger.critical(u"%r get err:%s" % (self, err))
			raise Http404


class TicketOutputView(View):

	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(TicketOutputView, self).dispatch(*args, **kwargs)


	def get(self, request, *args, **kwargs):
		access_key = kwargs.get('access_key', None)
		if not access_key or not SHA1_RE.search(access_key):
			raise Http404
		try:
			ticketpass = TicketPass.objects.get(owner=request.user, access_key__exact=access_key)
			ticket = open(ticketpass.get_file_path(), 'r') #TODO: avoid direct media directory access
			response = HttpResponse(ticket, mimetype='application/pdf')
			response['Content-Disposition'] = 'attachment; filename=%s' % (smart_str(ticketpass.title))
			return response
		except TicketPass.DoesNotExist:
			return HttpResponse(u"门票不存在")
		except Exception, err:
			logger.critical(u"%r get err:%s" % (self, err))
			raise Http404



class DigitalFileDownloadView(View):

	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DigitalFileDownloadView, self).dispatch(*args, **kwargs)


	def get(self, request, *args, **kwargs):
		access_key = kwargs.get('access_key', None)
		if not access_key or not SHA1_RE.search(access_key):
			raise Http404
		try:
			digitalfilepass = DigitalFilePass.objects.get(owner=request.user, access_key__exact=access_key)
			digital_file = open(digitalfilepass.get_file_path(), 'r') #TODO: avoid direct media directory access
			response = HttpResponse(digital_file, mimetype='application/force-download')
			response['Content-Disposition'] = 'attachment; filename=%s.pdf' % (smart_str(digitalfilepass.title)) #TODO: assume this is pdf type
			# It's usually a good idea to set the 'Content-Length' header too.
			# You can also set any other required headers: Cache-Control, etc.
			return response
		except DigitalFilePass.DoesNotExist:
			return HttpResponse(u"虚拟物品不存在")
		except Exception, err:
			logger.critical(u"%r get err:%s" % (self, err))
			raise Http404



class TicketDownloadView(View):

	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(TicketDownloadView, self).dispatch(*args, **kwargs)


	def get(self, request, *args, **kwargs):
		access_key = kwargs.get('access_key', None)
		if not access_key or not SHA1_RE.search(access_key):
			raise Http404
		try:
			ticketpass = TicketPass.objects.get(owner=request.user, access_key__exact=access_key)
			ticket = open(ticketpass.get_file_path(), 'r') #TODO: avoid direct media directory access
			response = HttpResponse(ticket, mimetype='application/pdf')
			response['Content-Disposition'] = 'attachment; filename=%s' % (smart_str(u"ticket:%s_%s_%s.pdf" % (ticketpass.event_id, ticketpass.owner_id, ticketpass.pk))) #TODO: assume this is pdf type
			# It's usually a good idea to set the 'Content-Length' header too.
			# You can also set any other required headers: Cache-Control, etc.
			return response
		except TicketPass.DoesNotExist:
			return HttpResponse(u"门票不存在")
		except Exception, err:
			logger.critical(u"%r get err:%s" % (self, err))
			raise Http404

#TODO: 门票认证，返回httpresponse, 只接受 get method
class TicketPassVerifyView(View):
	"""
	用来作为手机应用验证门票合法性app
	"""

	http_method_names = ['get']

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(TicketVerifyView, self).dispatch(*args, **kwargs)

	def get(self, request, *args, **kwargs):
		# <view logic>
		distributor = self.request.user # 缓存用户

		owner = kwargs.get('owner', None)
		ticket_id = kwargs.get('ticket_id', None)
		event_id = kwargs.get('event_id', None)

		status, reply = Ticket.objects.verify_ticket(owner, distributor, event_id)

		if status:
			HttpResponse('success')
		else:
			return HttpResponse(u'fail: %s' % reply)




