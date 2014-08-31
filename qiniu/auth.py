# -*- coding: utf-8 -*-

import hmac
import time
from hashlib import sha1
from base64 import urlsafe_b64encode

from requests.auth import AuthBase
from requests.compat import urlparse
from requests.compat import is_py2

from .exceptions import DeprecatedApi

_policyFields = {
    'callbackUrl',
    'callbackBody',
    'callbackHost',

    'returnUrl',
    'returnBody',

    'endUser',
    'saveKey',
    'insertOnly',

    'detectMime',
    'mimeLimit',
    'fsizeLimit',

    'persistentOps',
    'persistentNotifyUrl',
    'persistentPipeline',
}

_deprecatedPolicyFields = {
    'asyncOps'
}


class Auth(object):

    def __init__(self, accessKey, secretKey):
        self.__checkKey(accessKey, secretKey)
        self.__accessKey, self.__secretKey = accessKey, secretKey

    def __token(self, data):
        key = self.__secretKey
        if not is_py2:
            if isinstance(data, str):
                data = bytes(data, 'utf-8')
            key = bytes(self.__secretKey, 'utf-8')
        hashed = hmac.new(key, data, sha1)
        return str(urlsafe_b64encode(hashed.digest()))

    def token(self, data):
        return '%s:%s' % (self.__accessKey, self.__token(data))

    def tokenWithData(self, data):
        if not is_py2:
            data = bytes(data, 'utf-8')
        data = urlsafe_b64encode(data)
        return '%s:%s:%s' % (self.__accessKey, str(self.__token(data)), data)

    def tokenOfRequest(self, url, body=None, content_type=None):
        parsedUrl = urlparse(url)
        query = parsedUrl.query
        path = parsedUrl.path
        data = path
        if query != '':
            data = ''.join([data, '?', query])
        data = ''.join([data, "\n"])

        if body:
            mimes = [
                'application/x-www-form-urlencoded',
            ]
            if content_type in mimes:
                data += body

        return '%s:%s' % (self.__accessKey, self.__token(data))

    def __checkKey(self, accessKey, secretKey):
        if not (accessKey and secretKey):
            raise ValueError('invalid key')

    def privateDownloadUrl(self, url, expires=3600):
        '''
         *  return private url
        '''

        deadline = int(time.time()) + expires
        if '?' in url:
            url += '&'
        else:
            url += '?'
        url = '%se=%s' % (url, str(deadline))

        token = self.token(url)
        return '%s&token=%s' % (url, token)

    def uploadToken(self, bucket, key=None, policy=None, expires=3600):
        if bucket is None or bucket == '':
            raise ValueError('invalid bucket name')

        scope = bucket
        if key is not None:
            scope = bucket + ':'

        args = dict(
            scope=scope,
            deadline=int(time.time()) + expires,
        )

        if policy is not None:
            self.__copyPolicy(policy, args)

        data = json.dumps(args, separators=(',', ':'))
        return self.tokenWithData(data)

    def __copyPolicy(self, policy, to):
        for k, v in policy.items():
            if k in _deprecatedPolicyFields:
                raise DeprecatedApi(v + 'is deprecated')
            if k in _policyFields:
                to[k] = v


class RequestsAuth(AuthBase):
    def __init__(self, auth):
        self.auth = auth

    def __call__(self, r):
        token = self.auth.tokenOfRequest(r.url)
        r.headers['Authorization'] = 'QBox %s' % token
        return r
