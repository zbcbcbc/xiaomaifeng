# -*- coding: utf-8 -*-
# 
# Copyright 2013 XiaoMaiFeng


__version__ = '1.1.2'
__author__ = 'Liao Xuefeng (askxuefeng@gmail.com)'
__editor__ = 'Bicheng Zhang'

'''
Python client SDK for douban API using OAuth 2.
'''


try:
    import json
except ImportError:
    import simplejson as json

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import gzip, time, hmac, base64, hashlib, urllib, urllib2, logging, mimetypes, collections, datetime

from config import *



class DoubanAPIError(StandardError):
    '''
    raise DoubanAPIError if receiving json message indicating failure.
    '''
    def __init__(self, error_code, error, request):
        self.error_code = error_code #code
        self.error = error #msg
        self.request = request
        StandardError.__init__(self, error)

    def __unicode__(self):
        return u'DoubanAPIError: %s: %s, request: %s' % (self.error_code, self.error, self.request)


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


def _encode_params(**kw):
    '''
    do url-encode parameters

    >>> _encode_params(a=1, b='R&D')
    'a=1&b=R%26D'
    >>> _encode_params(a=u'\u4e2d\u6587', b=['A', 'B', 123])
    'a=%E4%B8%AD%E6%96%87&b=A&b=B&b=123'
    '''
    args = []
    for k, v in kw.iteritems():
        if isinstance(v, basestring):
            qv = v.encode('utf-8') if isinstance(v, unicode) else v
            args.append('%s=%s' % (k, urllib.quote(qv)))
        elif isinstance(v, collections.Iterable):
            for i in v:
                qv = i.encode('utf-8') if isinstance(i, unicode) else str(i)
                args.append('%s=%s' % (k, urllib.quote(qv)))
        else:
            qv = str(v)
            args.append('%s=%s' % (k, urllib.quote(qv)))
    return '&'.join(args)

# CJ done
def _encode_multipart(**kw):
    ' build a multipart/form-data body with randomly generated boundary '
    boundary = '----------%s' % hex(int(time.time() * 1000))
    data = []
    for k, v in kw.iteritems():
        data.append('--%s' % boundary)
        if hasattr(v, 'read'):
            # file-like object:
            filename = getattr(v, 'name', '')
            content = v.read()
            data.append('Content-Disposition: form-data; name="%s"; filename="hidden"' % k)
            data.append('Content-Length: %d' % len(content))
            data.append('Content-Type: %s' % _guess_content_type(filename))
            data.append('Content-Transfer-Encoding: binary\n')
            data.append(content)
        else:
            data.append('Content-Disposition: form-data; name="%s"\r\n' % k)
            data.append(v.encode('utf-8') if isinstance(v, unicode) else v)
    data.append('--%s--\r\n' % boundary)
    return '\r\n'.join(data), boundary
# CJ done
def _guess_content_type(url):
    n = url.rfind('.')
    if n==(-1):
        return 'application/octet-stream'
    ext = url[n:].lower()
    # mimetyeps.types_map keys are stored in lower case, ex: '.jpeg'
    return mimetypes.types_map.get(ext, 'application/octet-stream')

_HTTP_GET = 0
_HTTP_POST = 1
_HTTP_UPLOAD = 2
_HTTP_DELETE = 3

def _http_delete(url, authorization, **kw):
    logging.info('DELETE %s' % url)
    return _http_call(url, _HTTP_DELETE, authorization, **kw)

def _http_get(url, authorization=None, **kw):
    logging.info('GET %s' % url)
    return _http_call(url, _HTTP_GET, authorization, **kw)

def _http_post(url, authorization=None, **kw):
    logging.info('POST %s' % url)
    return _http_call(url, _HTTP_POST, authorization, **kw)

def _http_upload(url, authorization=None, **kw):
    logging.info('MULTIPART POST %s' % url)
    return _http_call(url, _HTTP_UPLOAD, authorization, **kw)

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

# need working on delete !!!
def _http_call(the_url, method, authorization, **kw):
    '''
    send an http request and return a json object if no error occurred.
    '''
    # working for photo upload, mind for other calls
    params = None
    boundary = None
    if method==_HTTP_UPLOAD:
        # fix sina upload url:
        #the_url = the_url.replace('https://api.', 'https://upload.api.')
        params, boundary = _encode_multipart(**kw)
    else:
        params = _encode_params(**kw)
        if '/remind/' in the_url:
            # fix sina remind api:
            the_url = the_url.replace('https://api.', 'https://rm.api.')
    http_url = '%s?%s' % (the_url, params) if method==_HTTP_GET else the_url
    http_body = None if method==_HTTP_GET else params
    req = urllib2.Request(http_url, data=http_body)
    req.add_header('Accept-Encoding', 'gzip')
    if authorization:
        req.add_header('Authorization', 'Bearer %s' % authorization)
    if boundary:
        req.add_header('Content-Type', 'multipart/form-data; boundary=%s' % boundary)
    try:
        resp = urllib2.urlopen(req)
        body = _read_body(resp)
        r = _parse_json(body)
        if hasattr(r, 'code'):# !!! code 106 means token expire ???
            raise DoubanAPIError(r.code, r.get('msg', ''), r.get('request', ''))
        return r
    except urllib2.HTTPError, e:
        try:
            r = _parse_json(_read_body(e))
        except:
            r = None
        if hasattr(r, 'code'):
            raise DoubanAPIError(r.code, r.get('msg', ''), r.get('request', ''))
        raise DoubanAPIError(e.code, e, '')
    except urllib2.URLError, e:
        print 'Douban urllib2 URLError'
        raise DoubanAPIError('Douban urllib2 URLError', e, '')




_METHOD_MAP = { 'GET': _HTTP_GET, 'POST': _HTTP_POST, 'UPLOAD': _HTTP_UPLOAD }


"""
以上属于原作者撰写，以下是新添加
"""

# CJ done
def douban_execute_api(access_token, path, method, **kw):
    """
    豆瓣执行API, 深度整合测试中
    """
    print u'Testing executing new doubanAPI>>>'
    method = _METHOD_MAP[method]
    if method == _HTTP_POST and 'image' in kw:
        method = _HTTP_UPLOAD
    return _http_call('%s%s' % (DOUBAN_API_URL, path), method, access_token, **kw)


#CJ done
def douban_get_authorize_url(**kwargs):
    '''
    return the authorization url that the user should be redirected to.
    '''
    redirect_uri = kwargs.get('redirect_uri', None)
    redirect = redirect_uri or DOUBAN_CALLBACK_URL
    return '%s%s?%s' % (DOUBAN_AUTHORIZATION_URI, 'auth', \
                _encode_params(client_id = DOUBAN_APP_KEY, \
                        response_type = DOUBAN_RESPONSE_TYPE, \
                        scope = DOUBAN_SCOPE, \
                        redirect_uri = redirect, **kwargs))


def douban_request_access_token(code, **kwargs):
    '''
    return access token as a JsonDict: 
    {"access_token":"your-access-token","expires_in":12345678,"uid":1234}, expires_in is represented using standard unix-epoch-time
    '''
    redirect_uri = kwargs.get('redirect_uri', None)
    redirect = redirect_uri or DOUBAN_CALLBACK_URL
    if not redirect:
        raise DoubanAPIError('21305', 'Parameter absent: redirect_uri', 'OAuth2 request')
    r = _http_post('%s%s' % (DOUBAN_AUTHORIZATION_URI, 'token?'), \
            client_id = DOUBAN_APP_KEY, \
            client_secret = DOUBAN_APP_SECRET, \
            redirect_uri = redirect, \
            code = code, grant_type = 'authorization_code')
    #current = int(time.time())
    #expires_in = r.expires_in + current

    #Those data are returned: douban_user_id, douban_user_name, refresh_token, expires_in, access_token

    return r


def douban_refresh_token(refresh_token):
    req_str = '%s%s' % (DOUBAN_AUTHORIZATION_URI, 'token?')
    r = _http_post(req_str, \
            client_id = DOUBAN_APP_KEY, \
            client_secret = DOUBAN_APP_SECRET, \
            refresh_token = refresh_token, \
            redirect_uri = DOUBAN_CALLBACK_URL, \
            grant_type = 'refresh_token')
    current = int(time.time())
    expires = r.expires_in + current
    # r should return access_token, expires_in, refresh_token, douban_user_id
    '''
    DOUBAN has NO remind_in
    remind_in = r.get('remind_in', None)
    if remind_in:
        rtime = int(remind_in) + current
        if rtime < expires:
            expires = rtime
    '''

    return JsonDict(access_token=r.access_token, refresh_token=r.refresh_token, expires=expires, expires_in=expires, uid=r.get('douban_user_id', None))

# ?? revoke oauth2 same as revoke token
def douban_revoke_oauth2(access_token):
    return _http_delete('%s%s' % (DOUBAN_AUTHORIZATION_URI, 'access_token'), \
                access_token = access_token)


__all__ = ["DoubanAPIError", "douban_get_authorize_url", "douban_request_access_token", "douban_refresh_token", "douban_revoke_oauth2","douban_execute_api"]




