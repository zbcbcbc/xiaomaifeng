"""
A management command which deletes expired accounts (e.g.,
accounts which signed up but never activated) from the database.

Calls ``RegistrationProfile.objects.delete_expired_users()``, which
contains the actual logic for determining which accounts are deleted.

"""

from django.contrib.auth.models import User
from django.core.management.base import NoArgsCommand

from dashboard.listing.models import DigitalFileSupervisor



class Command(NoArgsCommand):
	help = "Delete expired user registrations from the database"

	def handle_noargs(self, **options):
		DigitalFileSupervisor.objects.clean_supervisors()