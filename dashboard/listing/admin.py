# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"



from django.contrib import admin

from dashboard.listing.models import PhysicalItem, DigitalItem, DonationFund, PaybackFund, EventItem, DigitalFileSupervisor



class PhysicalItemAdmin(admin.ModelAdmin): 
	model = PhysicalItem
	#TODO: show image detail and selling detail
	readonly_fields = ('user', 'image', )
	search_fields = ['id', 'user__username', 'user__email', ]






class DigitalItemAdmin(admin.ModelAdmin): 
	model = DigitalItem
	readonly_fields = ('user' ,'image', 'digital_file', )
	search_fields = ['id', 'user__username', 'user__email', ]





class EventItemAdmin(admin.ModelAdmin):
	model = EventItem
	readonly_fields = ('id', 'user' ,'image', 'get_event_attenders')
	search_fields = ['id', 'user__username', 'user__email', ]




class DonationFundAdmin(admin.ModelAdmin): 
	model = DonationFund
	readonly_fields = ('user' ,'image',)
	search_fields = ['id', 'user__username', 'user__email', ]






class PaybackFundAdmin(admin.ModelAdmin): 
	model = PaybackFund
	readonly_fields = ('user' ,'image',)
	search_fields = ['id', 'user__username', 'user__email', ]





class DigitalFileSupervisorAdmin(admin.ModelAdmin):
	model = DigitalFileSupervisor
	readonly_fields = ('digital_item', 'digital_file', )
	search_fields = ['id', 'digital_item__id', ]





admin.site.register(PhysicalItem, PhysicalItemAdmin)
admin.site.register(DigitalItem, DigitalItemAdmin)
admin.site.register(EventItem, EventItemAdmin)
admin.site.register(DonationFund, DonationFundAdmin)
admin.site.register(PaybackFund, PaybackFundAdmin)
admin.site.register(DigitalFileSupervisor, DigitalFileSupervisorAdmin)

