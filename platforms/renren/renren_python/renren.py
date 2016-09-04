#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013, XiaoMaiFeng"




try:
	import json
except ImportError:
	import simplejson as json

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

import gzip, time, hmac, base64, hashlib, urllib, urllib2, logging, mimetypes, collections, datetime, logging, string

from config import *
import requests

logger = logging.getLogger('site.api.renren')


_HTTP_GET = 0
_HTTP_POST = 1
_HTTP_UPLOAD = 2

_METHOD_MAP = { 'GET': _HTTP_GET, 'POST': _HTTP_POST, 'UPLOAD': _HTTP_UPLOAD }


class RenRenAPIError(StandardError):
	def __init__(self, error_code, error, request):
		self.error_code = error_code
		self.error = error
		self.request = request
		StandardError.__init__(self, error)
	def __unicode__(self):
		return u'RenRenAPIError: %s: %s, request: %s' % (self.error_code, self.error, self.request)


'''
def _http_get(url, authorization=None, **kw):
	logging.info('GET %s' % url)
	return _http_call(url, _HTTP_GET, authorization, **kw)

def _http_post(url, authorization=None, **kw):
	logging.info('POST %s' % url)
	return _http_call(url, _HTTP_POST, authorization, **kw)

def _http_upload(url, authorization=None, **kw):
	logging.info('MULTIPART POST %s' % url)
	return _http_call(url, _HTTP_UPLOAD, authorization, **kw)

def _parse_json(s):
	' parse str into JsonDict '
	
	def _obj_hook(pairs):
		' convert json object to python object '
		o = JsonDict()
		for k, v in pairs.iteritems():
			o[str(k)] = v
		return o
	return json.loads(s, object_hook=_obj_hook)

class JsonDict(dict):
    ' general json object that allows attributes to be bound to and also behaves like a dict '
	
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(r"'JsonDict' object has no attribute '%s'" % attr)
	
    def __setattr__(self, attr, value):
        self[attr] = value

def _read_body(obj):
	using_gzip = obj.headers.get('Content-Encoding', '')=='gzip'
	body = obj.read()
	if using_gzip:
		logging.info('gzip content received.')
		gzipper = gzip.GzipFile(fileobj=StringIO(body))
		fcontent = gzipper.read()
		gzipper.close()
		return fcontent
	return body
'''
"""
以上代码请勿随意改动
"""




	
def renren_http_call(access_token, path, orig_method, mac_key=None, nonce_digits=5, **kw):
	"""
	人人执行API, 深度整合测试中
	支持Bear 和 mac authorization
	只抛出RenRenAPIError
	"""
	header = {}
	params = {}
	# hash method
	method = _METHOD_MAP[orig_method]
	
	# 组合api地址
	the_url = '%s%s' % (RENREN_API_URL, path) # example: 'api.renren.com/v2/user'

	http_url = the_url

	logger.debug('renren_http_call >>> http_url: %s' % http_url)

	header['Accept-Encoding'] = 'gzip'

	# 添加authorization 
	if mac_key:
		#建立mac hash
		nonce = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(nonce_digits)) # 默认5位随机数
		ts = int((datetime.datetime.now() - datetime.datetime(1970, 1, 1, 0, 0)).total_seconds()) # 时间戳
		request_url =  '%s?%s' % (path, params) if params else path # if no params, don't add ?
		constructed_string = "%s\n%s\n%s\n%s\n%s\n%s\n" % (ts, nonce, orig_method, request_url, RENREN_API_RAW_URL, RENREN_API_PORT)
		mac = hmac.new(mac_key) # 创建mac
		mac = mac.update(constructed_string, digestmod=hashlib.sha1)
		
		logger.info('renren_http_call >>> mac auth >>> constructed:%s,mac:%s' % (constructed_string,mac))

		header['Authorization'] = 'MAC id=%s,ts=%s,nonce=%s,mac=%s' % (access_token,ts,nonce,mac)
	else:
		# Bear 方法
		header['Authorization'] =  'Bearer %s' % access_token

	for k, v in kw.iteritems():
		if k == 'file':
			pic = {'file':v}
		else:
			params[k] = v
	# 打开url
	try:
		if method == _HTTP_POST and 'file' in kw:
			r = requests.post(http_url, data=params, headers = header, files = pic)
		elif method == _HTTP_GET:
			r = requests.get(http_url, params= params, headers = header)
		else:
			r = requests.post(http_url, data= params, headers = header)
		print r.status_code

		r_json = r.json()

		logger.debug('renren_http_call >>> return_json: %s' % r_json)

		if r_json.__contains__('error'):
			# there is an error code
			raise RenRenAPIError(r_json['error']['code'], r_json['error']['message'], r.status_code)
			#return r_json['error']
		# if not http error: return result
		return r_json['response']
	except requests.exceptions.ConnectionError, e:
		logger.critical(u"renren_http_call: connectionError")
		raise RenRenAPIError(u'requests.exceptions.ConnectionError', e, None)
	except requests.exceptions.RequestException, e:
		logger.info(u"renren_http_call :requests.exceptions.RequestException >> %s" %e)
		raise RenRenAPIError(u'requests.exceptions.RequestException', e, None)
	except requests.exceptions.TooManyRedirects, e:
		logger.info(u"renren_http_call: Too many redirects >> %s" %e)
		raise RenRenAPIError(u'requests.exceptions.TooManyRedirects', e, None)
	except requests.exceptions.URLRequired, e:
		logger.info(u"renren_http_call: URL is absent >> %s" %e)
		raise RenRenAPIError(u'requests.exceptions.URLRequired', e, None)
	except RenRenAPIError as e:
		logger.info(u"renren_http_call: RenRenAPIError >> %s" %e)
		raise RenRenAPIError(e.error_code, e.error, e.request)
	except Exception, err:
		logger.info(u"renren_http_call: unexpected error %s" %err)
		raise RenRenAPIError(u'unkown code', str(err), type(err))




def get_renren_authorize_url(mac=False, **kwargs):
	"""
	支持mac和bearer
	"""

	redirect_uri = kwargs.get('redirect_uri', None)
	redirect = redirect_uri or RENREN_CALLBACK_URL
	args = dict(client_id=RENREN_APP_API_KEY, redirect_uri=redirect)
	args["response_type"] = RENREN_RESPONSE_TYPE
	args["scope"] = RENREN_SCOPE
	args["state"] = "1 23 abc&?|."

	if mac:
		args["token_type"] = 'mac'
	
	return RENREN_AUTHORIZATION_URI + "?" + urllib.urlencode(args)




def request_renren_access_token(code, mac=False, **kwargs):
	"""
	目前不支持mac, return data package: expires_in, refresh_token, access_token
	"""

	redirect_uri = kwargs.get('redirect_uri', None)
	redirect = redirect_uri or RENREN_CALLBACK_URL
	if not redirect:
		raise RenRenAPIError('21305', 'Parameter absent: redrect_uri', None)
	
	args = dict(client_id=RENREN_APP_API_KEY, redirect_uri=redirect)
	args["client_secret"] = RENREN_APP_SECRET_KEY
	args["code"] = code
	if mac:
		args["grant_type"] = "client_credentials"
		args["token_type"] = 'mac'
	else:
		args["grant_type"] = "authorization_code"
	# Obtain access token
	try:
		r = requests.post(RENREN_ACCESS_TOKEN_URI, data = args)
		r_json = r.json()
		if r_json.__contains__('error'):
			#{\n  "error": "invalid_client",\n  "error_code": 20100,\n  "error_description": "Invalid client_id: null"\n}
			raise RenRenAPIError(r_json['error_code'], r_json['error_description'], r_json['error'])

	except requests.exceptions.ConnectionError, e:
		logger.critical(u"renren_http_call: connectionError")
		raise RenRenAPIError(u'requests.exceptions.ConnectionError', e, None)
	except requests.exceptions.RequestException, e:
		logger.info(u"renren_http_call :requests.exceptions.RequestException >> %s" %e)
		raise RenRenAPIError(u'requests.exceptions.RequestException', e, None)
	except requests.exceptions.TooManyRedirects, e:
		logger.info(u"renren_http_call: Too many redirects >> %s" %e)
		raise RenRenAPIError(u'requests.exceptions.TooManyRedirects', e, None)
	except requests.exceptions.URLRequired, e:
		logger.info(u"renren_http_call: URL is absent >> %s" %e)
		raise RenRenAPIError(u'requests.exceptions.URLRequired', e, None)
	except RenRenAPIError as e:
		logger.info(u"renren_http_call: RenRenAPIError >> %s" %e)
		raise RenRenAPIError(e.error_code, e.error, e.request)
	except Exception, err:
		logger.info(u"renren_http_call: unexpected error %s" %err)
		raise RenRenAPIError(u'unkown code', str(err), type(err))
	else:
		return r_json


def renren_refresh_token(refresh_token):
	'''
	Bearer 类型 access token的refresh, return package: access_token, expires_in, refresh_token, scope
	'''
	args = {'grant_type': 'refresh_token'}
	args['refresh_token'] = refresh_token
	args['client_id'] = RENREN_APP_API_KEY
	args['client_secret'] = RENREN_APP_SECRET_KEY
	url = RENREN_ACCESS_TOKEN_URI
	try:
		r = requests.post(url, data=args)
		r_json = r.json()
		if r_json.__contains__('error'):
			#{\n  "error": "invalid_request",\n  "error_description": "The request is missing a required parameter: client_secret"\n}
			raise RenRenAPIError(r.status_code, r_json['error_description'], r_json['error'])

		return r_json
	except requests.exceptions.ConnectionError, e:
		logger.critical(u"renren_http_call: no internet connection")
		raise RenRenAPIError(u'requests.exceptions.ConnectionError, 无网络链接', e, None)
	except requests.exceptions.RequestException, e:
		logger.info(u"renren_http_call :requests.exceptions.RequestException >> %s" %e)
		raise RenRenAPIError(u'requests.exceptions.RequestException', e, None)
	except requests.exceptions.TooManyRedirects, e:
		logger.info(u"renren_http_call: Too many redirects >> %s" %e)
		raise RenRenAPIError(u'requests.exceptions.TooManyRedirects', e, None)
	except requests.exceptions.URLRequired, e:
		logger.info(u"renren_http_call: URL is absent >> %s" %e)
		raise RenRenAPIError(u'requests.exceptions.URLRequired', e, None)
	except RenRenAPIError as e:
		logger.info(u"renren_http_call: RenRenAPIError >> %s" %e)
		raise RenrenAPIError(e.error_code, e.error, e.request)
	except Exception, err:
		logger.info(u"renren_http_call: unexpected error %s" %err)
		raise RenRenAPIError(u'unkown code', str(err), type(err))




__all__ = ["RenRenAPIError", "get_renren_authorize_url", "request_renren_access_token", "renren_http_call"]



