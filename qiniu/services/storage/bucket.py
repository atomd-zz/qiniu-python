# -*- coding: utf-8 -*-

import requests

from qiniu import config
from qiniu.auth import RequestsAuth

from qiniu.utils import base64Encode, _ret


class Bucket(object):

    def __init__(self, bucket=None, auth=None):
        self.auth = auth
        self.bucket = bucket

    def list(self, prefix=None, marker=None, limit=None):
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

        url = 'http://%s/list' % config.RSF_HOST

        r = requests.get(
            url, params=options, auth=RequestsAuth(self.auth), timeout=config._connectionTimeout)
        ret = _ret(r)

        eof = False

        if ret and not ret.get('marker'):
            eof = True

        return ret, eof

    def stat(self, keys):
        url = None
        params = None
        if isinstance(keys, str):
            resource = self.__entry(keys)
            url = 'http://%s/stat/%s' % (config.RS_HOST, resource)
        else:
            ops = []
            for key in keys:
                ops.append("/stat/%s" % self.__entry(key))
            url = 'http://%s/batch' % config.RS_HOST
            params = dict(op=ops)

        r = requests.post(
            url, data=params, auth=RequestsAuth(self.auth), timeout=config._connectionTimeout)
        return _ret(r)

    def delete(self, keys):
        url = None
        params = None
        if isinstance(keys, str):
            resource = self.__entry(keys)
            url = 'http://%s/delete/%s' % (config.RS_HOST, resource)
        else:
            ops = []
            for key in keys:
                ops.append("/delete/%s" % self.__entry(key))
            url = 'http://%s/batch' % config.RS_HOST
            params = dict(op=ops)

        r = requests.post(
            url, data=params, auth=RequestsAuth(self.auth), timeout=config._connectionTimeout)
        return _ret(r)

    def move(self, keyPairs, targetBucket=None):
        ops = []
        url = 'http://%s/batch' % config.RS_HOST
        for k, v in keyPairs.items():
            to = _entry(v, targetBucket) if targetBucket else self.__entry(v)
            ops.append("/move/%s/%s" % (self.__entry(k), to))

        r = requests.post(
            url, data=dict(op=ops), auth=RequestsAuth(self.auth), timeout=config._connectionTimeout)
        return _ret(r)

    def copy(self, keyPairs, targetBucket=None):
        ops = []
        url = 'http://%s/batch' % config.RS_HOST
        for k, v in keyPairs.items():
            to = _entry(v, targetBucket) if targetBucket else self.__entry(v)
            ops.append("/copy/%s/%s" % (self.__entry(k), to))

        r = requests.post(
            url, data=dict(op=ops), auth=RequestsAuth(self.auth), timeout=config._connectionTimeout)
        return _ret(r)

    def fetch(self, url, key):
        to = self.__entry(key)
        resource = base64Encode(url)
        cmd = 'http://%s/fetch/%s/to/%s' % (config.IO_HOST, resource, to)

        r = requests.post(
            cmd, auth=RequestsAuth(self.auth), timeout=config._connectionTimeout)
        return _ret(r)

    def prefetch(self, key):
        resource = self.__entry(key)
        url = 'http://%s/prefetch/%s' % (config.IO_HOST, resource)

        r = requests.post(url, auth=RequestsAuth(self.auth))
        return _ret(r)

    def buckets(self):
        url = 'http://%s/buckets' % config.RS_HOST

        r = requests.post(url, auth=RequestsAuth(self.auth), timeout=config._connectionTimeout)
        return _ret(r)

    def __entry(self, key):
        return _entry(self.bucket, key)


def _entry(bucket, key):
    return base64Encode('%s:%s' % (bucket, key))
