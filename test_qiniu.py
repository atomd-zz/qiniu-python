import unittest

import pytest

from qiniu import auth
from qiniu import utils

class AuthTestCase(unittest.TestCase):
    accessKey = 'abcdefghklmnopq'
    secretKey = '1234567890'
    mac = auth.Auth(accessKey, secretKey)

    def test_token(self):
        token = self.mac.token('test')
        assert token == 'abcdefghklmnopq:mSNBTR7uS2crJsyFr2Amwv1LaYg='

    def test_tokenWithData(self):
        token = self.mac.tokenWithData('test')
        assert token == 'abcdefghklmnopq:-jP8eEV9v48MkYiBGs81aDxl60E=:dGVzdA=='

    def test_noKey(self):
        with pytest.raises(ValueError):
            auth.Auth().token('nokey')
            auth.Auth('', '').token('nokey')

    def test_tokenOfRequest(self):
        token = self.mac.tokenOfRequest('http://www.qiniu.com?go=1', 'test', '')
        assert token == 'abcdefghklmnopq:cFyRVoWrE3IugPIMP5YJFTO-O-Y='
        token = self.mac.tokenOfRequest('http://www.qiniu.com?go=1', 'test', 'application/x-www-form-urlencoded')
        assert token == 'abcdefghklmnopq:svWRNcacOE-YMsc70nuIYdaa1e4='


class StorageTestCase(unittest.TestCase):
    def __init__(self):
        super(AuthTestCase, self).__init__()
        self.accessKey = 'abcdefghklmnopq'
        self.secretKey = '1234567890'
        self.mac = Auth(self.accessKey, self.secretKey)



class UtilsTestCase(object):
    def test_etag():
        pass


if __name__ == '__main__':
    unittest.main()
