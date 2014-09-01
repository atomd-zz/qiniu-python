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

from qiniu import Bucket, DeprecatedApi, Auth, put, utils, consts

from requests.compat import is_py2

if is_py2:
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
        self.assertEqual(err is consts.EOF or err is None, True)
        assert len(ret.get('items')) >= 1

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


def randomString(length):
    lib = string.ascii_uppercase
    return ''.join([random.choice(lib) for i in range(0, length)])


class UploaderTestCase(unittest.TestCase):

    mime_type = "text/plain"
    params = {'x:a': 'a'}
    q = Auth(accessKey, secretKey)

    def test_put(self):
        key = 'a\\b\\c"你好' + randomString(9)
        data = 'hello bubby!'
        crc32 = utils.crc32(data)
        token = self.q.uploadToken(bucketName)
        ret, err = put(token, key, data, crc32=crc32)
        assert err is None
        assert ret['key'] == key

    def test_putFile(self):
        localfile = '%s' % __file__
        key = "test_%s" % randomString(9)

        token = self.q.uploadToken(bucketName)
        crc32 = utils.fileCrc32(localfile)
        ret, err = put(token, key, open(localfile, 'rb'), crc32=crc32)
        assert err is None
        assert ret['key'] == key

    def test_putInvalidCrc(self):
        key = 'test_%s' % randomString(9)
        data = 'hello bubby!'
        crc32 = 'wrong crc32'
        token = self.q.uploadToken(bucketName)
        ret, err = put(token, key, data, crc32=crc32)
        # assert err is not None


class ResumableUploaderTestCase(unittest.TestCase):
    def __init__(self, arg):
        super(ResumableUploaderTestCase, self).__init__()
        self.arg = arg

if __name__ == '__main__':
    unittest.main()
