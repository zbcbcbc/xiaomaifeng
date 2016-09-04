# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"

import uuid, logging, os, datetime
import hashlib, re, random
from cStringIO import StringIO
from reportlab.pdfgen import canvas

from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import get_current_site
from django.db import models, transaction
from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.dispatch import receiver
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from notification import models as notification
from siteutils.signalutils import receiver_subclasses
from dashboard.passbook import qrcode
from siteutils.modelfields import TimeZoneField
from payment.alipay.modelfields import AlipaySubjectField
 

logger = logging.getLogger('xiaomaifeng.passbook')

"""
Set default storage
"""

if hasattr(settings, "AWS_SECRET_ACCESS_KEY"):
	try:
		from backends.S3Storage import S3Storage
		storage = S3Storage()
	except ImportError:
		raise S3BackendNotFound
else:
	storage = default_storage



# 决定qr_image path
def get_qr_image_path(instance, filename):
	#filename = os.path.basename(filename)
	#ext = filename.split('.')[-1].lower()
	#filename = "%s.%s" % (uuid.uuid4(), ext)
	return os.path.join('qrcode/owner', str(instance.owner.id), 'qrcode', filename)


 
class UrlQRCode(models.Model):
	"""
	Bare UrlQRCode abstract Model
	"""

	# it can store
	# url
	# image
	# contact info

	url = models.URLField(max_length=255, null=False, editable=True)
	qr_image = models.ImageField(
		upload_to=get_qr_image_path,
		height_field="qr_image_height",
		width_field="qr_image_width",
		null=True,
		blank=True,
		editable=True
	)
	qr_image_height = models.PositiveIntegerField(null=True, blank=True, editable=True)
	qr_image_width = models.PositiveIntegerField(null=True, blank=True, editable=True)

	class Meta:
		abstract = True

	def __unicode__(self):
		return "qrcode: %s:%s" % (self.pk, self.url)

	def __repr__(self):
		return u"%s:(%s)" % (self.__class__.__name__, self.pk)


	def get_absolute_url(self):
		raise NotImplementedError

	def qr_code(self):
		return u'%s' % self.qr_image.url
	
	qr_code.allow_tags = True





class FilePassBaseModel(UrlQRCode):

	owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, related_name="%(class)s_owner", editable=False)
	distributor = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, related_name="%(class)s_distributor", editable=False)
	title = AlipaySubjectField(null=False, editable=True) # max_length=128
	
	access_key = models.CharField(_('access key'), unique=True, max_length=40, null=False, editable=False)
	

	class Meta(UrlQRCode.Meta):
		abstract = True


	def deliver_to_owner(self):
		raise NotImplementedError

	def get_file_path(self):
		raise NotImplementedError

	def get_file_absolute_url(self):
		raise NotImplementedError

	def get_file_output_path(self):
		raise NotImplementedError


	def get_file_output_absolute_url(self):
		"""
		"""
		absolute_url = u"http://%s%s" % (Site.objects.get_current(), self.get_file_output_path())

		return absolute_url		


	def get_file_download_path(self):
		raise NotImplementedError


	def get_file_download_absolute_url(self):
		"""
		"""
		absolute_url = u"http://%s%s" % (Site.objects.get_current(), self.get_file_download_path())

		return absolute_url		



class TicketPassManager(models.Manager):

	def create_ticketpass(self, order, owner, event, deliver=False, **kwargs):
		"""
		返回ticketpass,失败返回None
		不检查活动开始日期结束日期，假设活动日期是正确的
		"""
		logger.info(u"%r creating ticketpass for %r..." % (event, owner))

		with transaction.commit_manually():
			try:
				sid = transaction.savepoint() # item reserve transaction savepoint
				if owner.id == event.user_id:
					raise Exception(u"门票出售者:%s和购买者:%s不能同一人" % (owner, distributor))

				access_key = self._generate_access_key(order, owner, event)

				ticket_pass = self.create(owner=owner, 
								distributor=event.user,
								event=event,
								title=event.name,
								url=reverse('dashboard:passbook:ticket-output', args=[access_key]), #WARNING, STUB,
								access_key=access_key,
								event_start=event.event_start, #WARNING, STUB
								time_zone=event.time_zone) #WARNING STUB)
								#digital_file=self.digital_file #TODO 同时给digital file url

				ticket = ticket_pass.generate_ticket_pdf()	

			except Exception, err:
				logger.critical(u"%r create ticketpass fail，reason:%s" % (self, err))
				transaction.savepoint_rollback(sid)
				ticket_pass = None
			finally:
				transaction.commit()
				if ticket_pass and deliver: ticket_pass.deliver_to_owner()
				return ticket_pass

	def _generate_access_key(self, order, owner, event):
		"""
		"""
		salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
		ticket_unique = u"%s%s%s" % (order.pk, event.pk, event.name)
		if isinstance(ticket_unique, unicode):
			ticket_unique = ticket_unique.encode('utf-8')
		access_key = hashlib.sha1(salt+ticket_unique).hexdigest()
		return access_key



	def get_tickets_to_send_event_start_notification(self, hours=2, **kwargs):
		"""
		找到即将发生的活动并给拥有者发送提醒
		STUB
		TODO: Timezone convertion!
		"""
		return None
		#tickets = self.filter(event_start__range=[])

	def verify_ticket(self, ticket_id, distributor_id, event_id=None, security_key=None):
		"""
		认证门票是否属于对应活动而且门票没有被使用过也没有过期
		回复(认证结果(Boolean), 信息(String))
		#TODO: add security_key
		#TODO event_id is a great way to cache ticket since there will be burst of people
		veriying ticket
		"""
		logger.info(u"用户(%s)的活动认证的门票(%s)中..." % (distributor_id, ticket_id))

		try:
			ticket = self.select_for_update().get(pk=ticket_id)
		except ObjectDoesNotExist, err:
			return (False, u"门票不存在")
		except Exception, err:
			logger.critical(u"用户(%s)的活动(%s)认证门票(%s)失败，原因:%s" % (distributor_id, event_id, ticket_id, err))
			return (False, u"认证失败")
		else:
			if distributor_id != ticket.distributor_id:
				return (False, u"不是售票者无法验证门票")
			if not ticket.is_used:
				ticket.is_used = True
				ticket.save()
				return (True, None)
			else:
				return (False, u'门票已经被使用过')	


	def delete_used_ticket(self):
		"""
		删除被使用过的tickets
		注意：强行删除，不能还原
		"""
		logger.info(u"删除使用过的所有门票中...")

		tickets = self.filter(is_used=True)

		for ticket in tickets:
			ticket.delete()


def _get_ticketpass_pdf_path(instance, filename):
	#filename = os.path.basename(filename)
	#ext = filename.split('.')[-1].lower()
	#filename = "%s.%s" % (uuid.uuid4(), ext)
	return os.path.join('ticketpass/owner', str(instance.owner.id), 'ticket', filename)


class TicketPass(FilePassBaseModel):

	ticket = models.FileField(null=True, storage=storage, upload_to=_get_ticketpass_pdf_path)
	event = models.ForeignKey('listing.EventItem', null=True, on_delete=models.SET_NULL, editable=True)
	event_start = models.DateTimeField(null=False, editable=True)
	time_zone = TimeZoneField(null=True, editable=True)
	is_used = models.BooleanField(default=False, null=False, editable=True)

	objects = TicketPassManager()

	class Meta(FilePassBaseModel.Meta):
		#TODO: WARNING, time-zone unaware
		ordering = ['event_start']
		unique_together = (('owner', 'distributor', 'event'), )


	def __unicode__(self):
		return "%s(%s)" % (self.__class__.__name__, self.pk)

	def get_absolute_url(self):
		return reverse('dashboard:passbook:ticketpass-detail', args=[str(self.pk)])


	def generate_ticket_pdf(self):
		"""
		generate ticket pdf here
		Throw error to upper level
		"""
		tmp = StringIO()
		ticket_pdf_name = u"%s_%s_%s.pdf" % (self.owner_id, self.title, self.pk)
		ticket_pdf = canvas.Canvas(tmp)
		ticket_pdf.drawString(100, 100, "lalala") #TODO: can't identify unicode
		ticket_pdf.showPage()
		ticket_pdf.save()
		ticket_pdf_content = ContentFile(tmp.getvalue())
		tmp.close()
		self.ticket.save(ticket_pdf_name, ticket_pdf_content, save=True)
		return self.ticket


	def deliver_to_owner(self):
		"""
		把自己发送给拥有者
		不返回
		"""
		logger.info(u"delivering %r to %r ..." % (self, self.owner))

		try:
			notification.send([self.owner], "deliver_ticketpass", {"title":self.title})
		except Exception, err:
			logger.critical(u"%s邮件QR门票给%s的邮箱失败，原因: %s" % (self, self.owner, err))     
			pass


	def get_file_path(self):
		return self.ticket.path

	def get_file_absolute_url(self):
		return self.ticket.url


	def get_file_output_path(self):
		return reverse('dashboard:passbook:ticket-output', args=[str(self.access_key)])


	def get_file_download_path(self):
		return reverse('dashboard:passbook:ticket-download', args=[str(self.access_key)])			


@receiver(models.signals.pre_delete, sender=TicketPass, weak=False, dispatch_uid='passbook.signals.pre_delete_ticketpass')
def pre_delete_ticketpass(sender, instance, using, **kwargs):
	"""
	Clear stored pdf before model being deleted
	"""
	try:
		ticket_pdf = open(instance.ticket.url)
		if ticket_pdf:
			ticket_pdf.delete()
	except IOError, err:
		logger.warning(u"%r:%s" % (pre_delete_ticketpass, err))
	except Exception, err:
		logger.critical(u"%r:%s" % (pre_delete_ticketpass, err))


class DigitalFilePassManager(models.Manager):

	
	def create_digitalfilepass(self, order, owner, digital_item, deliver=False, **kwargs):
		"""
		"""
		access_key = self._generate_access_key(order, owner, digital_item)

		try:
			from dashboard.listing.models import DigitalFileSupervisor
			digital_file_supervisor = DigitalFileSupervisor.objects.get(digital_item=digital_item)

			digitalfile_pass = self.create(owner=owner,
							distributor=digital_item.user,
							title=digital_item.name,
							url=reverse('dashboard:passbook:digitalfile-download', args=['access_key']), #TODO avoid direct media directory access
							digital_file_supervisor=digital_file_supervisor,
						   	access_key=access_key)

		except Exception, err:
			logger.critical(u"%r fail, reason:%s" % (create_digitalfilepass, err))
			digitalfile_pass = None
		finally:
			if digitalfile_pass and deliver:
				digitalfile_pass.deliver_to_owner()

			return digitalfile_pass

	def _generate_access_key(self, order, owner, digital_item):
		"""
		"""
		salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
		digital_file_unique = u"%s%s%s" % (order.pk, digital_item.pk, digital_item.name)
		if isinstance(digital_file_unique, unicode):
			digital_file_unique = digital_file_unique.encode('utf-8')
		access_key = hashlib.sha1(salt+digital_file_unique).hexdigest()
		return access_key



class DigitalFilePass(FilePassBaseModel):

	digital_file_supervisor = models.ForeignKey('listing.DigitalFileSupervisor', null=False, on_delete=models.CASCADE, editable=True)
	objects = DigitalFilePassManager()

	def __unicode__(self):
		#TODO: 
		return "%s(%s)" % (self.__class__.__name__, self.pk)

	def __repr__(self):
		return "%s(%s)" % (self.__class__.__name__, self.pk)

	def get_absolute_url(self):
		return reverse('dashboard:passbook:digitalfilepass-detail', args=[str(self.pk)])


	def deliver_to_owner(self):
		"""
		把自己发送给拥有者
		不返回
		"""
		logger.info(u"delivering %r to %r ..." % (self, self.owner))

		try:
			notification.send([self.owner], "deliver_digitalfilepass", {"title":self.title})
		except Exception, err:
			logger.critical(u"%s邮件QR门票给%s的邮箱失败，原因: %s" % (self, self.owner, err))     
			pass


	def get_file_path(self):
		"""
		"""
		return self.digital_file_supervisor.get_digital_file_path()


	def get_file_absolute_url(self):
		"""
		"""
		return self.digital_file_supervisor.get_digital_file_absolute_url()


	def get_file_output_path(self):
		"""
		"""
		return reverse('dashboard:passbook:digitalfile-output', args=[str(self.access_key)])


	def get_file_download_path(self):

		return reverse('dashboard:passbook:digitalfile-download', args=[str(self.access_key)])




@receiver_subclasses(models.signals.pre_save, UrlQRCode, 'passbook.signals.pre_save_urlqrcode', weak=False)
def pre_save_urlqrcode(sender, instance, **kwargs):    

	#logger.info(u"%spre_save signal arrived..." % (instance))
	
	if not instance.pk:
		instance._QRCODE = True
	else:
		if hasattr(instance, '_QRCODE'):
			instance._QRCODE = False
		else:
			instance._QRCODE = True


@receiver_subclasses(models.signals.post_save, UrlQRCode, 'passbook.signals.post_save_urlqrcode', weak=False)
def post_save_urlqrcode(sender, instance, **kwargs):
	"""
	根据模型创建QRCode
	"""
	#logger.info(u"%spost_save signal arrived..." % (instance))

	if instance._QRCODE:
		instance._QRCODE = False
		if instance.qr_image:
			instance.qr_image.delete()
		qr = qrcode.QRCode(4, qrcode.ERROR_CORRECT_L)
		qr.add_data(instance.url)
		#print 'data added..'
		qr.make()
		#print 'image made..'
		image = qr.make_image()

		#print 'image madelll'
 
		#Save image to string buffer
		image_buffer = StringIO()
		image.save(image_buffer)
		image_buffer.seek(0)
 
		#Here we use django file storage system to save the image.
		file_name = 'UrlQR_%s.jpg' % instance.id
		file_object = File(image_buffer, file_name)
		content_file = ContentFile(file_object.read())
		instance.qr_image.save(file_name, content_file, save=True)


