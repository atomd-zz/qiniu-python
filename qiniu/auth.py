# -*- coding: utf-8 -*-

import hmac
import time
from hashlib import sha1

from .compat import is_py2, urlparse, json, b

from requests.auth import AuthBase

from .exceptions import DeprecatedApi
from .utils import base64Encode


_policyFields = set([
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
])

_deprecatedPolicyFields = set([
    'asyncOps'
])


class Auth(object):

    def __init__(self, accessKey, secretKey):
        self.__checkKey(accessKey, secretKey)
        self.__accessKey, self.__secretKey = accessKey, secretKey
        self.__secretKey = b(self.__secretKey)

    def __token(self, data):
        data = b(data)
        hashed = hmac.new(self.__secretKey, data, sha1)
        return base64Encode(hashed.digest())

    def token(self, data):
        return '{0}:{1}'.format(self.__accessKey, self.__token(data))

    def tokenWithData(self, data):
        data = base64Encode(data)
        return '{0}:{1}:{2}'.format(self.__accessKey, self.__token(data), data)

    def tokenOfRequest(self, url, body=None, contentType=None):
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
            if contentType in mimes:
                data += body

        return '{0}:{1}'.format(self.__accessKey, self.__token(data))

    @staticmethod
    def __checkKey(accessKey, secretKey):
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
        url = '{0}e={1}'.format(url, str(deadline))

        token = self.token(url)
        return '{0}&token={1}'.format(url, token)

    def uploadToken(self, bucket, key=None, expires=3600, policy=None, strictPolicy=True):
        if bucket is None or bucket == '':
            raise ValueError('invalid bucket name')

        scope = bucket
        if key is not None:
            scope = '{0}:{1}'.format(bucket, key)

        args = dict(
            scope=scope,
            deadline=int(time.time()) + expires,
        )

        if policy is not None:
            self.__copyPolicy(policy, args, strictPolicy)

        data = json.dumps(args, separators=(',', ':'))
        return self.tokenWithData(data)

    @staticmethod
    def __copyPolicy(policy, to, strictPolicy):
        for k, v in policy.items():
            if k in _deprecatedPolicyFields:
                raise DeprecatedApi(k)
            if (not strictPolicy) or k in _policyFields:
                to[k] = v


class RequestsAuth(AuthBase):
    def __init__(self, auth):
        self.auth = auth

    def __call__(self, r):
        token = None
        if r.body is not None and r.headers['Content-Type'] == 'application/x-www-form-urlencoded':
            token = self.auth.tokenOfRequest(r.url, r.body, 'application/x-www-form-urlencoded')
        else:
            token = self.auth.tokenOfRequest(r.url)
        r.headers['Authorization'] = 'QBox {0}'.format(token)
        return r
