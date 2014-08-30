import os

import unittest
import pytest

from qiniu.auth import Auth
import qiniu.utils
from qiniu.exceptions import DeprecatedApi
from qiniu.center import Qiniu

accessKey = os.getenv("QINIU_ACCESS_KEY")
secretKey = os.getenv("QINIU_SECRET_KEY")

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


class centerTestCase(unittest.TestCase):
    q = Qiniu(dummyAccessKey, dummySecretKey)
    def test_deprecatedPolicy(self):
        with pytest.raises(DeprecatedApi):
            self.q.uploadToken('1', None, {'asyncOps': 1})


class StorageTestCase(unittest.TestCase):
    mac = Auth(accessKey, secretKey)


if __name__ == '__main__':
    unittest.main()
