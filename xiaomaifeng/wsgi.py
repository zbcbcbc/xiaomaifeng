"""
WSGI config for jifu project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"


import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weijiaoyi.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
