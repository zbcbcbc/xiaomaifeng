"""
A management command which deletes expired accounts (e.g.,
accounts which signed up but never activated) from the database.

Calls ``RegistrationProfile.objects.delete_expired_users()``, which
contains the actual logic for determining which accounts are deleted.

"""

from django.contrib.auth.models import User
from django.core.management.base import NoArgsCommand, CommandError

from dashboard.orders.models import Order



class Command(NoArgsCommand):
	help = "Delete expired orders and corresponding payment from the database"

	def handle_noargs(self, **options):
		Order.objects.delete_expired_orders()


