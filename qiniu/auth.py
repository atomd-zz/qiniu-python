from urlparse import urlparse
import hmac
from hashlib import sha1
from base64 import urlsafe_b64encode


class Auth(object):

    def __init__(self, accessKey, secretKey):
        self.__checkKey(accessKey, secretKey)
        self.__accessKey, self.__secretKey = accessKey, secretKey

    def __token(self, data):
        hashed = hmac.new(self.__secretKey, data, sha1)
        return urlsafe_b64encode(hashed.digest())

    def token(self, data):
        return '%s:%s' % (self.__accessKey, self.__token(data))

    def tokenWithData(self, data):
        data = urlsafe_b64encode(data)
        return '%s:%s:%s' % (self.__accessKey, self.__token(data), data)

    def tokenOfRequest(self, url, body, content_type):
        parsedUrl = urlparse(url)
        query = parsedUrl.query
        path = parsedUrl.path
        data = path
        if query != '':
            data = ''.join([data, '?', query])
        data = ''.join([data, "\n"])

        if body:
            mimes = [
                'application/x-www-form-urlencoded',
            ]
            if content_type in mimes:
                data += body

        return '%s:%s' % (self.__accessKey, self.__token(data))

    def __checkKey(self, accessKey, secretKey):
        if accessKey is None or secretKey is None or (accessKey == '' or secretKey == ''):
            raise ValueError('invalid key')
