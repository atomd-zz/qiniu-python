# -*- coding: utf-8 -*-

import requests

from qiniu import config
from qiniu.auth import RequestsAuth

from qiniu.utils import urlsafe_base64_encode, _ret, entry


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

        url = 'http://{0}/list'.format(config.RSF_HOST)

        r = self.__get(url, options)
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
            url = 'http://{0}/stat/{1}'.format(config.RS_HOST, resource)
        else:
            ops = []
            for key in keys:
                ops.append("/stat/{0}".format(self.__entry(key)))

            url = 'http://{0}/batch'.format(config.RS_HOST)
            params = dict(op=ops)

        r = self.__post(url, params)
        return _ret(r)

    def delete(self, keys):
        url = None
        params = None
        if isinstance(keys, str):
            resource = self.__entry(keys)
            url = 'http://{0}/delete/{1}'.format(config.RS_HOST, resource)
        else:
            ops = []
            for key in keys:
                ops.append("/delete/{0}".format(self.__entry(key)))
            url = 'http://{0}/batch'.format(config.RS_HOST)
            params = dict(op=ops)

        r = self.__post(url, params)
        return _ret(r)

    def move(self, key_pairs, target_bucket=None):
        ops = []
        url = 'http://{0}/batch'.format(config.RS_HOST)
        for k, v in key_pairs.items():
            to = entry(v, target_bucket) if target_bucket else self.__entry(v)
            ops.append("/move/{0}/{1}".format(self.__entry(k), to))

        r = self.__post(url, dict(op=ops))
        return _ret(r)

    def copy(self, key_pairs, target_bucket=None):
        ops = []
        url = 'http://{0}/batch'.format(config.RS_HOST)
        for k, v in key_pairs.items():
            to = entry(v, target_bucket) if target_bucket else self.__entry(v)
            ops.append("/copy/{0}/{1}".format(self.__entry(k), to))

        r = self.__post(url, dict(op=ops))
        return _ret(r)

    def fetch(self, url, key):
        to = self.__entry(key)
        resource = urlsafe_base64_encode(url)
        cmd = 'http://{0}/fetch/{1}/to/{2}'.format(config.IO_HOST, resource, to)
        r = self.__post(cmd)
        return _ret(r)

    def prefetch(self, key):
        resource = self.__entry(key)
        url = 'http://{0}/prefetch/{1}'.format(config.IO_HOST, resource)
        r = self.__post(url)
        return _ret(r)

    def buckets(self):
        url = 'http://{0}/buckets'.format(config.RS_HOST)
        r = self.__post(url)
        return _ret(r)

    def __entry(self, key):
        return entry(self.bucket, key)

    def __post(self, url, data=None):
        headers = {'User-Agent': config.USER_AGENT}
        return requests.post(
            url, data=data, auth=RequestsAuth(self.auth),
            timeout=config.get_default('connection_timeout'), headers=headers)

    def __get(self, url, params=None):
        headers = {'User-Agent': config.USER_AGENT}
        return requests.get(
            url, params=params, auth=RequestsAuth(self.auth),
            timeout=config.get_default('connection_timeout'), headers=headers)
