# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


from dashboard.passbook.models import TicketPass, DigitalFilePass
from dashboard.listing.models import DigitalFileSupervisor



class TicketPassAdmin(admin.ModelAdmin):
	model = TicketPass
	readonly_fields = ('owner', 'distributor', 'event', 'url', 'qr_image', 
						'qr_image_width', 'qr_image_height', 'access_key', 'is_used')
	#list_display = ('url', 'qr_code')
	search_fields = ['id', 'owner__id', 'owner__username', 'owner__first_name', 'owner__last_name', ]
	raw_id_fields = ['owner', 'distributor', 'event', ]
	actions = ['deliver_ticket',]
	can_delete = True

	def deliver_ticket(self, request, queryset):
		for ticket_pass in queryset:
			ticket_pass.deliver_to_owner()

	deliver_ticket.short_description = _(u"发送电子票给用户")




class DigitalFileSupervisorInline(admin.StackedInline):
	model = DigitalFileSupervisor
	raw_id_fields = ['digital_item', ]
	extra = 0
	max_num = 0
	can_delete = False

class DigitalFilePassAdmin(admin.ModelAdmin):
	model = DigitalFilePass
	readonly_fields = ('owner', 'distributor', 'digital_file_supervisor', 'url', 'qr_image', 'qr_image_width', 'qr_image_height', 'access_key')
	inlines = (DigitalFileSupervisorInline, )
	list_display = ('url', 'qr_code')
	search_fields = ['id', 'owner__id',]
	can_delete = True

	def deliver_digital_file(self, request, queryset):
		for digital_file_pass in queryset:
			digital_file_pass.deliver_to_owner()


admin.site.register(TicketPass, TicketPassAdmin)
admin.site.register(DigitalFilePass, DigitalFilePassAdmin)





