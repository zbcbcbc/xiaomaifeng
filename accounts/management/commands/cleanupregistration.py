# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng

"""
A management command which deletes expired accounts (e.g.,
accounts which signed up but never activated) from the database.

Calls ``RegistrationProfile.objects.delete_expired_users()``, which
contains the actual logic for determining which accounts are deleted.

"""

from django.contrib.auth.models import User
from django.core.management.base import NoArgsCommand

from accounts.models import RegistrationProfile



class Command(NoArgsCommand):
	help = "Delete expired user registrations from the database"

	def handle_noargs(self, **options):
		RegistrationProfile.objects.delete_expired_users()


	def delete_deactivated_users(self):
		"""
		彻底删除注销用户
		TODO
		"""
		users = User.objects.filter(is_activate=False)
		for user in users:
			user.delete() # TODO: delete all user related objects

	def deactivate_zombie_users(self):
		"""
		注销很久没有登陆的帐户
		TODO
		"""
		pass