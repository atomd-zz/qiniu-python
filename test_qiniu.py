# -*- coding: utf-8 -*-
# flake8: noqa
import os
import string
import random
import tempfile

import unittest
import pytest

from qiniu import DeprecatedApi, QiniuServiceException, Auth, set_default, etag
from qiniu import Bucket, put, putfile, resumable_put, resumable_putfile
from qiniu import urlsafe_base64_encode, urlsafe_base64_decode

from qiniu.compat import is_py2, b

from qiniu.services.storage.uploader import _put

import qiniu.config

if is_py2:
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')

access_key = os.getenv('QINIU_ACCESS_KEY')
secret_key = os.getenv('QINIU_SECRET_KEY')
bucket_name = os.getenv('QINIU_TEST_BUCKET')

dummyaccess_key = 'abcdefghklmnopq'
dummysecret_key = '1234567890'
dummyMac = Auth(dummyaccess_key, dummysecret_key)


def rand_string(length):
    lib = string.ascii_uppercase
    return ''.join([random.choice(lib) for i in range(0, length)])


def create_temp_file(size):
    t = tempfile.mktemp()
    f = open(t, 'wb')
    f.seek(size-1)
    f.write(b('0'))
    f.close()
    return t


def remove_temp_file(file):
    try:
        os.remove(file)
    except OSError:
        pass


class UtilsTest(unittest.TestCase):

    def test_urlsafe(self):
        a = '你好\x96'
        u = urlsafe_base64_encode(a)
        assert a == urlsafe_base64_decode(u)


class AuthTestCase(unittest.TestCase):

    def test_token(self):
        token = dummyMac.token('test')
        assert token == 'abcdefghklmnopq:mSNBTR7uS2crJsyFr2Amwv1LaYg='

    def test_token_with_data(self):
        token = dummyMac.token_with_data('test')
        assert token == 'abcdefghklmnopq:-jP8eEV9v48MkYiBGs81aDxl60E=:dGVzdA=='

    def test_noKey(self):
        with pytest.raises(ValueError):
            Auth(None, None).token('nokey')
        with pytest.raises(ValueError):
            Auth('', '').token('nokey')

    def test_token_of_request(self):
        token = dummyMac.token_of_request('http://www.qiniu.com?go=1', 'test', '')
        assert token == 'abcdefghklmnopq:cFyRVoWrE3IugPIMP5YJFTO-O-Y='
        token = dummyMac.token_of_request('http://www.qiniu.com?go=1', 'test', 'application/x-www-form-urlencoded')
        assert token == 'abcdefghklmnopq:svWRNcacOE-YMsc70nuIYdaa1e4='

    def test_deprecatedPolicy(self):
        with pytest.raises(DeprecatedApi):
            dummyMac.upload_token('1', None, policy={'asyncOps': 1})


class BucketTestCase(unittest.TestCase):
    q = Auth(access_key, secret_key)
    bucket = Bucket(bucket_name, q)

    def test_list(self):
        ret, eof = self.bucket.list(limit=4)
        assert eof is False
        assert len(ret.get('items')) == 4
        ret, eof = self.bucket.list(limit=100)
        assert eof is True

    def test_buckets(self):
        ret = self.bucket.buckets()
        assert bucket_name in ret

    def test_pefetch(self):
        ret = self.bucket.prefetch('python-sdk.html')
        assert ret == {}

    def test_fetch(self):
        ret = self.bucket.fetch('http://developer.qiniu.com/docs/v6/sdk/python-sdk.html', 'fetch.html')
        assert ret == {}

    def test_stat(self):
        ret = self.bucket.stat('python-sdk.html')
        assert 'hash' in ret
        ret = self.bucket.stat(['python-sdk.html'])
        assert 'hash' in ret[0]['data']

    def test_delete(self):
        with pytest.raises(QiniuServiceException):
            ret = self.bucket.delete('del')

        ret = self.bucket.delete(['del'])
        assert 612 == ret[0]['code'] and ret[0]['data']['error'] == 'no such file or directory'

    def test_move(self):
        key = 'copyto'+rand_string(8)
        self.bucket.copy({'copyfrom': key})
        ret = self.bucket.move({key: key + 'move'})
        assert ret[0]['code'] == 200
        ret = self.bucket.delete(key + 'move')
        assert ret == {}

    def test_copy(self):
        key = 'copyto'+rand_string(8)
        ret = self.bucket.copy({'copyfrom': key})
        assert ret[0]['code'] == 200
        ret = self.bucket.delete(key)
        assert ret == {}


class UploaderTestCase(unittest.TestCase):

    mime_type = "text/plain"
    params = {'x:a': 'a'}
    q = Auth(access_key, secret_key)

    def test_put(self):
        key = 'a\\b\\c"你好'
        data = 'hello bubby!'
        token = self.q.upload_token(bucket_name)
        ret = put(token, key, data)
        assert ret['key'] == key

        key = ''
        data = 'hello bubby!'
        token = self.q.upload_token(bucket_name, key)
        ret = put(token, key, data, check_crc=True)
        assert ret['key'] == key

    def test_putfile(self):
        localfile = __file__
        key = 'test_file'

        token = self.q.upload_token(bucket_name, key)
        ret = putfile(token, key, localfile, mime_type=self.mime_type, check_crc=True)
        assert ret['key'] == key
        assert ret['hash'] == etag(localfile)

    def test_putInvalidCrc(self):
        key = 'test_invalid'
        data = 'hello bubby!'
        crc32 = 'wrong crc32'
        token = self.q.upload_token(bucket_name)
        with pytest.raises(QiniuServiceException):
            _put(token, key, data, None, None, crc32=crc32)

    def test_putWithoutKey(self):
        key = None
        data = 'hello bubby!'
        token = self.q.upload_token(bucket_name)
        ret = put(token, key, data)
        assert ret['hash'] == ret['key']

        data = 'hello bubby!'
        token = self.q.upload_token(bucket_name, 'nokey2')

        with pytest.raises(QiniuServiceException):
            put(token, None, data)

    def test_retry(self):
        key = 'retry'
        data = 'hello retry!'
        set_default(default_up_host='a')
        token = self.q.upload_token(bucket_name)
        ret = put(token, key, data)
        assert ret['key'] == key
        qiniu.set_default(default_up_host=qiniu.config.UPAUTO_HOST)


class ResumableUploaderTestCase(unittest.TestCase):

    mime_type = "text/plain"
    params = {'x:a': 'a'}
    q = Auth(access_key, secret_key)

    def test_putfile(self):
        localfile = __file__
        key = 'test_file_r'

        token = self.q.upload_token(bucket_name, key)
        ret = resumable_putfile(token, key, localfile, self.params, self.mime_type)
        assert ret['key'] == key

    def test_big_file(self):
        key = 'big'
        token = self.q.upload_token(bucket_name, key)
        localfile = create_temp_file(4 * 1024 * 1024 + 1)
        notify = lambda progress, total: progress

        ret = resumable_putfile(token, key, localfile, self.params, self.mime_type, notify=notify)
        assert ret['key'] == key
        remove_temp_file(localfile)

    def test_retry(self):
        localfile = __file__
        key = 'test_file_r_retry'
        set_default(default_up_host='a')
        token = self.q.upload_token(bucket_name, key)
        ret = resumable_putfile(token, key, localfile, self.params, self.mime_type)
        assert ret['key'] == key
        qiniu.set_default(default_up_host=qiniu.config.UPAUTO_HOST)


if __name__ == '__main__':
    unittest.main()
