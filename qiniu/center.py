# -*- coding: utf-8 -*-

import time
import json

from qiniu.auth import Auth
from qiniu.exceptions import DeprecatedApi

from qiniu.services.storage.bucket import Bucket

RS_HOST = "rs.qbox.me"
RSF_HOST = "rsf.qbox.me"
UP_HOST = "up.qiniu.com"
UP_HOST2 = "upload.qiniu.com"
DEFAULT_TIMEOUT = 30
EOF = 'EOF'

_policyFields = [
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
]

_deprecatedPolicyFields = [
    'asyncOps'
]


class Qiniu(object):

    def __init__(self, accessKey, secretKey):
        self.__auth = Auth(accessKey, secretKey)

    def bucket(self, name):
        return Bucket(name, self.__auth)

    def buckets():
        pass

    def downloadUrlWithToken(self, url, expires=3600):
        '''
         *  return private url
        '''

        deadline = int(time.time()) + expires
        if '?' in url:
            url += '&'
        else:
            url += '?'
        url = '%se=%s' % (url, str(deadline))

        token = self.__auth.token(url)
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
        return self.__auth.tokenWithData(data)

    def __copyPolicy(self, policy, to):
        for v in _deprecatedPolicyFields:
            if v in policy:
                raise DeprecatedApi(v + 'is deprecated')

        for v in _policyFields:
            x = policy[v]
            if x is not None:
                to[v] = x
