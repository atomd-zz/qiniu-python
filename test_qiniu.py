# -*- coding: utf-8 -*-
import os

import string
import random

try:
    import zlib
    binascii = zlib
except ImportError:
    zlib = None
    import binascii

import unittest
import pytest

from qiniu import Bucket, DeprecatedApi, Auth, put, putFile

import qiniu.consts

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

accessKey = os.getenv("QINIU_ACCESS_KEY")
secretKey = os.getenv("QINIU_SECRET_KEY")
bucketName = os.getenv("QINIU_TEST_BUCKET")

dummyAccessKey = 'abcdefghklmnopq'
dummySecretKey = '1234567890'
dummyMac = Auth(dummyAccessKey, dummySecretKey)


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

    def test_listPrefix(self):
        ret, err = self.bucket.listByPrefix(limit=4)
        self.assertEqual(err is qiniu.consts.EOF or err is None, True)
        assert len(ret.get('items')) == 4


def r(length):
    lib = string.ascii_uppercase
    return ''.join([random.choice(lib) for i in range(0, length)])


class UploaderTestCase(unittest.TestCase):

    mime_type = "text/plain"
    params = {'x:a': 'a'}
    q = Auth(accessKey, secretKey)

    def test_put(self):
        key = 'a\\b\\c"你好' + r(9)
        data = 'hello bubby!'
        checkCrc = 2
        crc32 = binascii.crc32(data) & 0xFFFFFFFF
        token = self.q.uploadToken(bucketName)
        ret, err = put(token, key, data, checkCrc=2, crc32=crc32)
        assert err is None
        assert ret['key'] == key

    def test_putFile(self):
        localfile = '%s' % __file__
        key = "test_%s" % r(9)

        token = self.q.uploadToken(bucketName)
        ret, err = putFile(token, key, localfile, checkCrc=1)
        assert err is None
        assert ret['key'] == key

    def test_putInvalidCrc(self):
        key = 'test_%s' % r(9)
        data = 'hello bubby!'
        checkCrc = 2
        crc32 = 'wrong crc32'
        token = self.q.uploadToken(bucketName)
        ret, err = put(token, key, data, checkCrc=2, crc32=crc32)
        # assert err is not None


class ResumableUploaderTestCase(unittest.TestCase):
    def __init__(self, arg):
        super(ResumableUploaderTestCase, self).__init__()
        self.arg = arg

if __name__ == '__main__':
    unittest.main()
