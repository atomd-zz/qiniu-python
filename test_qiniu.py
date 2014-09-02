# -*- coding: utf-8 -*-
import os

import string
import random

import unittest
import pytest

from qiniu import Bucket, DeprecatedApi, Auth, put, resumablePut, utils

from requests.compat import is_py2

if is_py2:
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')

accessKey = os.getenv('QINIU_ACCESS_KEY')
secretKey = os.getenv('QINIU_SECRET_KEY')
bucketName = os.getenv('QINIU_TEST_BUCKET')

dummyAccessKey = 'abcdefghklmnopq'
dummySecretKey = '1234567890'
dummyMac = Auth(dummyAccessKey, dummySecretKey)


def randString(length):
    lib = string.ascii_uppercase
    return ''.join([random.choice(lib) for i in range(0, length)])


class AuthTestCase(unittest.TestCase):

    def test_token(self):
        token = dummyMac.token('test')
        assert token == 'abcdefghklmnopq:mSNBTR7uS2crJsyFr2Amwv1LaYg='

    def test_tokenWithData(self):
        token = dummyMac.tokenWithData('test')
        assert token == 'abcdefghklmnopq:-jP8eEV9v48MkYiBGs81aDxl60E=:dGVzdA=='

    def test_noKey(self):
        with pytest.raises(ValueError):
            Auth(None, None).token('nokey')
        with pytest.raises(ValueError):
            Auth('', '').token('nokey')

    def test_tokenOfRequest(self):
        token = dummyMac.tokenOfRequest('http://www.qiniu.com?go=1', 'test', '')
        assert token == 'abcdefghklmnopq:cFyRVoWrE3IugPIMP5YJFTO-O-Y='
        token = dummyMac.tokenOfRequest('http://www.qiniu.com?go=1', 'test', 'application/x-www-form-urlencoded')
        assert token == 'abcdefghklmnopq:svWRNcacOE-YMsc70nuIYdaa1e4='

    def test_deprecatedPolicy(self):
        with pytest.raises(DeprecatedApi):
            dummyMac.uploadToken('1', None, {'asyncOps': 1})


class BucketTestCase(unittest.TestCase):
    q = Auth(accessKey, secretKey)
    bucket = Bucket(bucketName, q)

    def test_list(self):
        ret, eof = self.bucket.list(limit=4)
        assert eof is False
        assert len(ret.get('items')) == 4
        ret, eof = self.bucket.list(limit=100)
        assert eof is True

    def test_buckets(self):
        ret = self.bucket.buckets()
        assert bucketName in ret

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
        ret = self.bucket.delete('del')
        assert ret['error'] == 'no such file or directory'
        ret = self.bucket.delete(['del'])
        assert 612 == ret[0]['code'] and ret[0]['data']['error'] == 'no such file or directory'

    def test_move(self):
        key = 'copyto'+randString(8)
        self.bucket.copy({'copyfrom': key})
        ret = self.bucket.move({key: key + 'move'})
        assert ret[0]['code'] == 200
        ret = self.bucket.delete(key + 'move')
        assert ret == {}

    def test_copy(self):
        key = 'copyto'+randString(8)
        ret = self.bucket.copy({'copyfrom': key})
        assert ret[0]['code'] == 200
        ret = self.bucket.delete(key)
        assert ret == {}


class UploaderTestCase(unittest.TestCase):

    mimeType = "text/plain"
    params = {'x:a': 'a'}
    q = Auth(accessKey, secretKey)

    def test_put(self):
        key = 'a\\b\\c"你好'
        data = 'hello bubby!'
        crc32 = utils.crc32(data)
        token = self.q.uploadToken(bucketName)
        ret, err = put(token, key, data, crc32=crc32)
        assert err is None
        assert ret['key'] == key

        key = ''
        data = 'hello bubby!'
        crc32 = utils.crc32(data)
        token = self.q.uploadToken(bucketName, key)
        ret, err = put(token, key, data, crc32=crc32)
        assert err is None
        assert ret['key'] == key

    def test_putFile(self):
        localfile = __file__
        key = 'test_file'

        token = self.q.uploadToken(bucketName, key)
        crc32 = utils.fileCrc32(localfile)
        ret, err = put(token, key, open(localfile, 'rb'), mimeType=self.mimeType, crc32=crc32)
        assert err is None
        assert ret['key'] == key

    def test_putInvalidCrc(self):
        key = 'test_invalid'
        data = 'hello bubby!'
        crc32 = 'wrong crc32'
        token = self.q.uploadToken(bucketName)
        ret, err = put(token, key, data, crc32=crc32)
        # assert err is not None

    def test_putWithoutKey(self):
        key = None
        data = 'hello bubby!'
        token = self.q.uploadToken(bucketName)
        ret, err = put(token, key, data)
        assert err is None
        assert ret['hash'] == ret['key']

        data = 'hello bubby!'
        token = self.q.uploadToken(bucketName, 'nokey2')
        ret, err = put(token, None, data)
        assert err is None
        assert ret['error'] is not None


class ResumableUploaderTestCase(unittest.TestCase):

    mimeType = "text/plain"
    params = {'x:a': 'a'}
    q = Auth(accessKey, secretKey)

    def test_putFile(self):
        localfile = __file__
        key = 'test_file_r'

        token = self.q.uploadToken(bucketName, key)
        reader = open(localfile, 'rb')
        size = os.stat(localfile).st_size
        ret, err = resumablePut(token, key, reader, size, self.params, self.mimeType)
        assert err is None
        assert ret['key'] == key


if __name__ == '__main__':
    unittest.main()
