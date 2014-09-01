# -*- coding: utf-8 -*-

import requests

from qiniu import consts
from qiniu.auth import RequestsAuth

from qiniu.utils import base64Encode


class Bucket(object):

    def __init__(self, bucket=None, auth=None):
        self.auth = auth
        self.bucket = bucket

    def listByPrefix(self, prefix=None, marker=None, limit=None):
        """前缀查询:
         * bucket => str
         * prefix => str
         * marker => str
         * limit => int
         * return ret => {'items': items, 'marker': markerOut}, err => str

        1. 首次请求 marker = None
        2. 无论 err 值如何，均应该先看 ret.get('items') 是否有内容
        3. 如果后续没有更多数据，err 返回 EOF，markerOut 返回 None（但不通过该特征来判断是否结束）
        """
        options = {
            'bucket': self.bucket,
        }
        if marker is not None:
            options['marker'] = marker
        if limit is not None:
            options['limit'] = limit
        if prefix is not None:
            options['prefix'] = prefix

        url = 'http://%s/list' % consts.RSF_HOST

        r = requests.get(url, params=options, auth=RequestsAuth(self.auth))
        ret = r.json()
        err = None
        if ret and not ret.get('marker'):
            err = qiniu.consts.EOF

        return ret, err

    def stat(self, keys):
        url = None
        params = None
        if isinstance(keys, str):
            resource = self.__entry(keys)
            url = 'http://%s/stat/%s' % (consts.RS_HOST, resource)
        else:
            ops = []
            for key in keys:
                ops.append("/stat/%s" % self.__entry(key))
            url = 'http://%s/batch' % consts.RS_HOST
            params = dict(op=ops)

        r = requests.post(url, data=params, auth=RequestsAuth(self.auth))
        ret = r.json()
        return ret

    def delete(self, keys):
        url = None
        params = None
        if isinstance(keys, str):
            resource = self.__entry(keys)
            url = 'http://%s/delete/%s' % (consts.RS_HOST, resource)
        else:
            ops = []
            for key in keys:
                ops.append("/delete/%s" % self.__entry(key))
            url = 'http://%s/batch' % consts.RS_HOST
            params = dict(op=ops)

        r = requests.post(url, data=params, auth=RequestsAuth(self.auth))
        ret = r.json()
        return ret

    def move(self, keyPairs, targetBucket=None):
        pass

    def copy(self, keyPairs, targetBucket=None):
        pass

    def fetch(self, url, key):
        to = self.__entry(key)
        resource = base64Encode(url)
        cmd = 'http://%s/fetch/%s/to/%s' % (consts.IO_HOST, resource, to)

        r = requests.post(cmd, auth=RequestsAuth(self.auth))
        ret = r.json()
        return ret

    def prefetch(self, key):
        resource = self.__entry(key)
        url = 'http://%s/prefetch/%s' % (consts.IO_HOST, resource)

        r = requests.post(url, auth=RequestsAuth(self.auth))
        ret = r.json()
        return ret

    def buckets(self):
        url = 'http://%s/buckets' % consts.RS_HOST

        r = requests.post(url, auth=RequestsAuth(self.auth))
        ret = r.json()
        return ret

    def __entry(self, key):
        return _entry(self.bucket, key)


def _entry(bucket, key):
    return base64Encode('%s:%s' % (bucket, key))
