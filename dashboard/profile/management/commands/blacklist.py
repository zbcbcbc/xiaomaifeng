"""
A management command find abnormal users and put them on blacklist

"""

from django.contrib.auth.models import User
from django.core.management.base import NoArgsCommand

from dashboard.profile.models import UserHealthProfile



class Command(NoArgsCommand):
	help = "Find abnormal users and put them on black list"

	def handle_noargs(self, **options):
		users = UserHealthProfile.objects.find_abnormal_users()
		for user in users:
			print user