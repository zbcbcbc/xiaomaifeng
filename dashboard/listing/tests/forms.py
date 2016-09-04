# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import logging, datetime
import pytz, mock

from django.utils import timezone as djtimezone
from django.test import TestCase
from django.core.files import File as dj_File
from django.contrib.auth.models import User
from django.db import IntegrityError

from dashboard.listing.forms import PhysicalItemForm, DigitalItemForm, DonationFundForm, PaybackFundForm, EventItemForm

logging.disable(logging.WARNING)


class TestPhysicalItemForm(TestCase):

	def setUp(self):
		self.invalid_data_dicts = [
			# name too long
			{'data': {'name':u'测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字', # 180
					'price':100, 
					'availability':100,
					'purchase_limit':10,
					'logistics_fee':10,
					'description':u'只是测试一下'},

			'error': ('name', [u'Ensure this value has at most 128 characters (it has 180).'])},

			# incorrect price
			# ---- negative
			{'data': {'name':u'测试一下',
					'price':-100, 
					'availability':100,
					'purchase_limit':10,
					'logistics_fee':10,
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure this value is greater than or equal to 0.01.'])},	

			# ---- too many decimal places
			{'data': {'name':u'测试一下',
					'price':0.001, 
					'availability':100,
					'purchase_limit':10,
					'logistics_fee':10,
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure that there are no more than 2 decimal places.'])},	

			# ---- too large (bigger than 1,000,000)	
			{'data': {'name':u'测试一下',
					'price':1000000.01, 
					'availability':100,
					'purchase_limit':10,
					'logistics_fee':10,
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure this value is less than or equal to 1000000.0.'])},

			# incorrect availability
			# ---- negative
			{'data': {'name':u'测试一下',
					'price':100, 
					'availability':-100,
					'purchase_limit':10,
					'logistics_fee':10,
					'description':u'只是测试一下'},
			'error': ('availability', [u'Ensure this value is greater than or equal to 0.'])},	

			# ---- integer only, no decimal places
			{'data': {'name':u'测试一下',
					'price':100, 
					'availability':9.1,
					'purchase_limit':10,
					'logistics_fee':10,
					'description':u'只是测试一下'},
			'error': ('availability', [u'Enter a whole number.'])},	

			# incorrect description
			# ---- too long (longer than 400 limit)
			{'data': {'name':u'测试一下',
					'price':100, 
					'availability':100,
					'purchase_limit':10,
					'logistics_fee':10,
					'description':u'测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字'}, # 874
			'error': ('description', [u'Ensure this value has at most 400 characters (it has 874).'])},									

			]
		
	def test_form(self):

		for invalid_dict in self.invalid_data_dicts:
			form = PhysicalItemForm(data=invalid_dict['data'])
			self.failIf(form.is_valid())
			self.assertEqual(form.errors[invalid_dict['error'][0]], invalid_dict['error'][1])

		# image	
		# TODO




class TestDigitalItemForm(TestCase):

	def setUp(self):
		mock_file = mock.Mock(spec=dj_File)
		print mock_file
		print type(mock_file)

	def test_form(self):
		pass



class TestEventItemForm(TestCase):

	def setUp(self):
		time_zone = pytz.timezone('Asia/Shanghai')
		expire_date = djtimezone.now().astimezone(time_zone)+datetime.timedelta(hours=12)
		event_start = expire_date + datetime.timedelta(hours=24)
		self.invalid_data_dicts = [
			# name too long
			{'data': {'name':u'测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字', # 180
					'price':100, 
					'availability':100,
					'purchase_limit':10,
					'expire_date':expire_date,
					'event_start':event_start,
					'description':u'只是测试一下'},

			'error': ('name', [u'Ensure this value has at most 128 characters (it has 180).'])},

			# incorrect price
			# ---- negative
			{'data': {'name':u'测试一下',
					'price':-100, 
					'availability':100,
					'purchase_limit':10,
					'expire_date':expire_date,
					'event_start':event_start,
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure this value is greater than or equal to 0.01.'])},	

			# ---- too many decimal places
			{'data': {'name':u'测试一下',
					'price':0.001, 
					'availability':100,
					'purchase_limit':10,
					'expire_date':expire_date,
					'event_start':event_start,
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure that there are no more than 2 decimal places.'])},	

			# ---- too large (bigger than 1,000,000)	
			{'data': {'name':u'测试一下',
					'price':1000000.01, 
					'availability':100,
					'purchase_limit':10,
					'expire_date':expire_date,
					'event_start':event_start,
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure this value is less than or equal to 1000000.0.'])},

			# incorrect availability
			# ---- negative
			{'data': {'name':u'测试一下',
					'price':100, 
					'availability':-100,
					'purchase_limit':10,
					'expire_date':expire_date,
					'event_start':event_start,
					'description':u'只是测试一下'},
			'error': ('availability', [u'Ensure this value is greater than or equal to 0.'])},	

			# ---- integer only, no decimal places
			{'data': {'name':u'测试一下',
					'price':100, 
					'availability':9.1,
					'purchase_limit':10,
					'expire_date':expire_date,
					'event_start':event_start,
					'description':u'只是测试一下'},
			'error': ('availability', [u'Enter a whole number.'])},	

			# incorrect description
			# ---- too long (longer than 400 limit)
			{'data': {'name':u'测试一下',
					'price':100, 
					'availability':100,
					'purchase_limit':10,
					'expire_date':expire_date,
					'event_start':event_start,
					'description':u'测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字'}, # 874
			'error': ('description', [u'Ensure this value has at most 400 characters (it has 874).'])},		

			]

	def test_form(self):
		for invalid_dict in self.invalid_data_dicts:
			form = EventItemForm(data=invalid_dict['data'])
			self.failIf(form.is_valid())
			self.assertEqual(form.errors[invalid_dict['error'][0]], invalid_dict['error'][1])

		# image	
		# TODO


class TestDonationFund(TestCase):

	def setUp(self):
		self.invalid_data_dicts = [
			# name too long
			{'data': {'name':u'测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字', # 180
					'price':100, 
					'goal':1000, 
					'description':u'只是测试一下'},

			'error': ('name', [u'Ensure this value has at most 128 characters (it has 180).'])},

			# incorrect price
			# ---- negative
			{'data': {'name':u'测试一下',
					'price':-100, 
					'goal':1000, 
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure this value is greater than or equal to 0.01.'])},	

			# ---- too many decimal places
			{'data': {'name':u'测试一下',
					'price':0.001, 
					'goal':1000, 
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure that there are no more than 2 decimal places.'])},	

			# ---- too large (bigger than 1,000,000)	
			{'data': {'name':u'测试一下',
					'price':1000000.01, 
					'goal':1000, 
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure this value is less than or equal to 1000000.0.'])},

			# incorrect goal
			# ---- negative
			{'data': {'name':u'测试一下',
					'price':100, 
					'goal':-100, 
					'description':u'只是测试一下'},
			'error': ('goal', [u'Ensure this value is greater than or equal to 0.'])},	

			# ---- integer only, no decimal places
			{'data': {'name':u'测试一下',
					'price':100, 
					'goal':0.001, 
					'description':u'只是测试一下'},
			'error': ('goal', [u'Enter a whole number.'])},	

			# incorrect description
			# ---- too long (longer than 400 limit)
			{'data': {'name':u'测试一下',
					'price':100, 
					'goal':100, 
					'description':u'测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字'}, # 874
			'error': ('description', [u'Ensure this value has at most 400 characters (it has 874).'])},									

			]



	def test_DonationFund_form(self):

		for invalid_dict in self.invalid_data_dicts:
			form = DonationFundForm(data=invalid_dict['data'])
			self.failIf(form.is_valid())
			self.assertEqual(form.errors[invalid_dict['error'][0]], invalid_dict['error'][1])

		# image	
		# TODO




class TestPaybackFund(TestCase):

	def setUp(self):
		self.invalid_data_dicts = [
			# name too long
			{'data': {'name':u'测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
											测试一下是不是只能收入小于一定的数量的汉字', # 180
					'price':100, 
					'goal':1000, 
					'description':u'只是测试一下'},

			'error': ('name', [u'Ensure this value has at most 128 characters (it has 180).'])},

			# incorrect price
			# ---- negative
			{'data': {'name':u'测试一下',
					'price':-100, 
					'goal':1000, 
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure this value is greater than or equal to 0.01.'])},	

			# ---- too many decimal places
			{'data': {'name':u'测试一下',
					'price':0.001, 
					'goal':1000, 
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure that there are no more than 2 decimal places.'])},	

			# ---- too large (bigger than 1,000,000)	
			{'data': {'name':u'测试一下',
					'price':1000000.01, 
					'goal':1000, 
					'description':u'只是测试一下'},
			'error': ('price', [u'Ensure this value is less than or equal to 1000000.0.'])},

			# incorrect goal
			# ---- negative
			{'data': {'name':u'测试一下',
					'price':100, 
					'goal':-100, 
					'description':u'只是测试一下'},
			'error': ('goal', [u'Ensure this value is greater than or equal to 0.'])},	

			# ---- integer only, no decimal places
			{'data': {'name':u'测试一下',
					'price':100, 
					'goal':0.001, 
					'description':u'只是测试一下'},
			'error': ('goal', [u'Enter a whole number.'])},	

			# incorrect description
			# ---- too long (longer than 400 limit)
			{'data': {'name':u'测试一下',
					'price':100, 
					'goal':100, 
					'description':u'测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字\
										测试一下是不是只能收入小于一定的数量的汉字测试一下是不是只能收入小于一定的数量的汉字'}, # 874
			'error': ('description', [u'Ensure this value has at most 400 characters (it has 874).'])},									

			]

	def test_form(self):
		# correct value
		for invalid_dict in self.invalid_data_dicts:
			form = PaybackFundForm(data=invalid_dict['data'])
			self.failIf(form.is_valid())
			self.assertEqual(form.errors[invalid_dict['error'][0]], invalid_dict['error'][1])

		# TODO: image	

