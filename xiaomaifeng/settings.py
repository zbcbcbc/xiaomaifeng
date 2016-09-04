"""
Django settings for weijiaoyi project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
__author__ = "Bicheng Zhang, Jian Chen "
__copyright__ = "Copyright 2013, XiaoMaiFeng"


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

import os, sys, logging
import djcelery

djcelery.setup_loader()


BASE_DIR = os.path.dirname(os.path.dirname(__file__))




# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'gx$eke^9n3iiutyv+hbh@!=#ic)ka-#so@$*ni7*+71t3b-a8c'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = False

"""
Test Setting
"""
TEST_CHARSET = 'utf-8'

ALLOWED_HOSTS = ['jchen93.webfactional.com']


# Application definition
INSTALLED_APPS = (
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	#'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'django.contrib.sites',
	'django.contrib.humanize', # used in django registration only 
	
	
	'djcelery',
	'metadata',
	'home',
	'notification',
	'accounts',
	'dashboard',
	'dashboard.orders',
	'dashboard.profile',
	'dashboard.listing',
	'dashboard.album',
	'dashboard.passbook',
	'platforms', 
	'platforms.weibo',
	'platforms.renren',
	'platforms.alipay',
	'platforms.douban',
	'payment',
	'payment.alipay',
	'siteutils',

	#'south',
)

MIDDLEWARE_CLASSES = (
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'debug_toolbar.middleware.DebugToolbarMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
	'django.middleware.transaction.TransactionMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
	"django.contrib.auth.context_processors.auth",
	"django.core.context_processors.debug",
	"django.core.context_processors.i18n",
	"django.core.context_processors.media",
	"django.core.context_processors.static",
	"django.core.context_processors.tz",
	"django.contrib.messages.context_processors.messages")


ROOT_URLCONF = 'xiaomaifeng.urls'

WSGI_APPLICATION = 'xiaomaifeng.wsgi.application'

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'xiaomaifeng_test_db',
		'USER': 'jchen93_test_ad',
		'PASSWORD': '1q2w3e4r',
		'HOST': 'localhost',
	}
}

"""
Templates
"""

TEMPLATE_DIRS = (
	BASE_DIR + '/templates/'
)

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

"""
Time zone setting
"""
USE_TZ = True
TIME_ZONE = 'Asia/Shanghai'

"""
Localization setting
"""
USE_I18N = True

USE_L10N = True

"""
Cached backend
"""
CACHES = {
	'default': {
		'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
		'LOCATION': 'unix:/home/jchen93/memcached.sock',
	}
}



AUTH_PROFILE_MODULE = 'dashboard.profile.UserProfile'
#AUTH_USER_MODEL = 'dashboard.MyUser'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/
"""
Static files and storage setting
"""
STATIC_URL = 'http://jchen93.webfactional.com/static/' # seperate static app setting
#STATIC_URL = '/static/'
STATIC_ROOT = '/home/jchen93/webapps/staticapp/'
LOGIN_URL = '/accounts/login/'
MEDIA_ROOT = '/home/jchen93/webapps/mediaapp/'
MEDIA_URL = 'http://jchen93.webfactional.com/media/'
LOGIN_REDIRECT_URL = '/dashboard/'


"""
Email settings
"""

EMAIL_HOST = 'smtp.webfaction.com'
EMAIL_HOST_USER = '' #TODO
EMAIL_HOST_PASSWORD = '' #TODO
DEFAULT_FROM_EMAIL = 'no-reply@weijiaoyi.com'
SERVER_EMAIL = 'no-reply@weijiaoyi.com'
NOTIFICATION_BACKENDS = [("no-reply@weijiaoyi.com", "notification.backends.email.EmailBackend"),]

INTERNAL_IPS = ('address',)

SITE_ID = 1

SESSION_ENGINE = ("django.contrib.sessions.backends.signed_cookies")
SESSION_COOKIE_HTTPONLY = True


"""
PAYMENT SETTING
"""
LOGGING_PAYMENT = 'payment.log'


"""
DJANGO LOGGING SETTING
"""
if DEBUG:
	# will output to your console
	logging.basicConfig(
		level = logging.INFO,
		format = '%(asctime)s %(levelname)s %(message)s',
	)


"""
Celery settings
"""
#celery settings
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = "redis://"

#celery optimizing
CELERY_DISABLE_RATE_LIMITS = True # However, renren needs rate limit, since it's unlink weibo with polling method
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = True

#celeryd setting

#CELERYD_OPTS="--verbosity=2 --beat --events"
CELERYD_NODES="w1"
CELERYD_USER="jchen93"
CELERYD_GROUP="jchen93"

CELERYD_LOG_LEVEL = "INFO"
CELERYD_CONCURRENCY = 1
CELERYD_FORCE_EXECV = True
CELERYD_TASK_SOFT_TIME_LIMIT = 10 #TODO

CELERYD_PID_FILE="/home/jchen93/var/run/celery/w1.pid"


#celery logging setting
#TODO
#celery security setting
#TODO

"""
registeration settings
"""
REGISTRATION_OPEN = False
ACCOUNT_ACTIVATION_DAYS = 2

"""
File upload setting
"""
#CONTENT_TYPES = ['image', 'video']
# 2.5MB - 2621440
# 5MB - 5242880
# 10MB - 10485760
# 20MB - 20971520
# 50MB - 5242880
# 100MB - 104857600
# 250MB - 214958080
# 500MB - 429916160
MAX_IMAGE_UPLOAD_SIZE = "5242880" #5MB
MAX_DIGITAL_FILE_UPLOAD_SIZE = "20971520" #20MB
#FILE_UPLOAD_MAX_MEMORY_SIZE = "5242880"
CONTENT_TYPES = ['application/pdf', 'audio/mpeg']

"""
RECAPTCHA settings
"""
RECAPTCHA_PUBLIC = '6LeEMOMSAAAAACNkudM37TiCyldakjQP6cZNZMVh'
RECAPTCHA_PRIVATE = '6LeEMOMSAAAAAJLdxzzlq0wAC33vZmVxyYQ6E7zy'




