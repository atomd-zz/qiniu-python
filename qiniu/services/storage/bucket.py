# -*- coding: utf-8 -*-

import requests

import qiniu.consts
from qiniu.auth import RequestsAuth


class Bucket(object):

    def __init__(self, bucket=None, auth=None):
        self.auth = auth
        self.bucket = bucket

    def put(self):
        pass

    def putFile(self):
        pass

    def resumablePut(self):
        pass

    def resumablePutFile(self):
        pass

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

        url = 'http://%s/list' % qiniu.consts.RSF_HOST

        r = requests.get(url, params=options, auth=RequestsAuth(self.auth))
        ret = r.json()
        err = None
        if ret and not ret.get('marker'):
            err = qiniu.consts.EOF

        return ret, err

    def stat(self, keys):
        return self.conn.call(uri_stat(self.bucket, key))

    def delete(self, keys):
        return self.conn.call(uri_delete(self.bucket, key))

    def move(self, keyPairs, targetBucket=None):
        return self.conn.call(uri_move(self.bucket, key_src, bucketDest, key_dest))

    def copy(self, keyPairs, targetBucket=None):
        return self.conn.call(uri_copy(self.bucket, key_src, bucketDest, key_dest))

    def fetch(self, key, url):
        pass

    def prefetch(self, url):
        pass


def __uri_stat(bucket, key):
    return "/stat/%s" % urlsafe_b64encode("%s:%s" % (bucket, key))


def __uri_delete(bucket, key):
    return "/delete/%s" % urlsafe_b64encode("%s:%s" % (bucket, key))


def __uri_move(bucket_src, key_src, bucketDest, key_dest):
    src = urlsafe_b64encode("%s:%s" % (bucket_src, key_src))
    dest = urlsafe_b64encode("%s:%s" % (bucketDest, key_dest))
    return "/move/%s/%s" % (src, dest)


def __uri_copy(bucket_src, key_src, bucketDest, key_dest):
    src = urlsafe_b64encode("%s:%s" % (bucket_src, key_src))
    dest = urlsafe_b64encode("%s:%s" % (bucketDest, key_dest))
    return "/copy/%s/%s" % (src, dest)
