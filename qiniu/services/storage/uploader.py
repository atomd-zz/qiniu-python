# -*- coding: utf-8 -*-

import os

import requests

from qiniu import config
from qiniu.utils import urlsafe_base64_encode, crc32, file_crc32, _ret, _file_iter
from qiniu.exceptions import QiniuServiceException, QiniuClientException

_session = None


def _init():
    global _session
    _session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=config.get_default('connection_pool'), pool_maxsize=config.get_default('connection_pool'),
        max_retries=config.get_default('connection_retries'))
    _session.mount('http://', adapter)


def _post(url, data=None, files=None, headers=None):
    if _session is None:
        _init()
    return _session.post(
        url, data=data, files=files, headers=headers, timeout=config.get_default('connection_timeout'))


def _need_retry(response, exception):
    if response is None:
        return True
    code = response.status_code
    if exception is None or code / 100 == 4 or code == 579 or code / 100 == 6 or code / 100 == 7:
        return False
    return True


def put(
        upToken, key, data, params=None, mimeType='application/octet-stream', checkCrc=False):
    ''' put data to Qiniu
    If key is None, the server will generate one.
    data may be str or read()able object.
    '''
    crc = crc32(data) if checkCrc else None
    return _put(upToken, key, data, params, mimeType, crc)


def putfile(
        upToken, key, filePath, params=None, mimeType='application/octet-stream', checkCrc=False):
    ''' put data to Qiniu
    If key is None, the server will generate one.
    data may be str or read()able object.
    '''
    crc = file_crc32(filePath) if checkCrc else None
    with open(filePath, 'rb') as input_stream:
            return _put(upToken, key, input_stream, params, mimeType, crc, isFile=True)


def _put(upToken, key, data, params, mimeType, crc32, isFile=False):
    fields = {}
    if params:
        for k, v in params.items():
            fields[k] = str(v)
    if crc32:
        fields['crc32'] = crc32
    if key is not None:
        fields['key'] = key
    fields['token'] = upToken
    url = 'http://' + config.get_default('default_up_host') + '/'
    name = key if key else 'filename'

    r = None
    exception = None
    headers = {'User-Agent': config.USER_AGENT}

    try:
        r = _post(url, data=fields, files={'file': (name, data, mimeType)}, headers=headers)
    except Exception as e:
        exception = e
    finally:
        retry = _need_retry(r, exception)

    if retry:
        url = 'http://' + config.UPBACKUP_HOST + '/'
        if isFile:
            data.seek(0)
        try:
            r = _post(url, data=fields, files={'file': (name, data, mimeType)}, headers=headers)
        except Exception as e:
            raise QiniuClientException(str(e))

    return _ret(r)


def resumable_put(upToken, key, input_stream, dataSize, params=None, mimeType=None):
    task = _Resume(upToken, key, input_stream, dataSize, params, mimeType)
    return task.upload()


def resumable_putfile(upToken, key, filePath, params=None, mimeType=None):
    ret = {}
    size = os.stat(filePath).st_size
    with open(filePath, 'rb') as input_stream:
        ret = resumable_put(upToken, key, input_stream, size, params, mimeType)
    return ret


class _Resume(object):

    def __init__(self, upToken, key, input_stream, dataSize, params, mimeType):
        self.upToken = upToken
        self.key = key
        self.input_stream = input_stream
        self.size = dataSize
        self.params = params
        self.mimeType = mimeType

    def upload(self):
        self.blockStatus = []

        for block in _file_iter(self.input_stream, config._BLOCK_SIZE):
            ret = self.makeBlock(block, len(block))
            self.blockStatus.append(ret)
        return self.makeFile()

    def makeBlock(self, block, blockSize):
        crc = crc32(block)
        block = bytearray(block)
        url = self.blockUrl(config.get_default('default_up_host'), blockSize)

        r = None
        exception = None
        try:
            r = self.post(url, block)
        except Exception as e:
            exception = e
        finally:
            retry = _need_retry(r, exception)

        if retry:
            url = self.blockUrl(config.UPBACKUP_HOST, blockSize)
            try:
                r = self.post(url, block)
            except Exception as e:
                raise QiniuClientException(str(e))

        ret = _ret(r)
        if ret['crc32'] != crc:
            raise QiniuServiceException(
                r.status_code, 'unmatch crc checksum', r.headers['X-Reqid'])
        return ret

    def blockUrl(self, host, size):
        return 'http://{0}/mkblk/{1}'.format(host, size)

    def makeFileUrl(self, host):
        url = ['http://{0}/mkfile/{1}'.format(host, self.size)]

        if self.mimeType:
            url.append('mimeType/{0}'.format(urlsafe_base64_encode(self.mimeType)))

        if self.key is not None:
            url.append('key/{0}'.format(urlsafe_base64_encode(self.key)))

        if self.params:
            for k, v in self.params.items():
                url.append('{0}/{1}'.format(k, urlsafe_base64_encode(v)))

        url = '/'.join(url)
        return url

    def makeFile(self):
        url = self.makeFileUrl(config.get_default('default_up_host'))
        body = ','.join([status['ctx'] for status in self.blockStatus])

        r = None
        exception = None
        try:
            r = self.post(url, body)
        except Exception as e:
            exception = e
        finally:
            retry = _need_retry(r, exception)

        if retry:
            url = self.makeFileUrl(config.UPBACKUP_HOST)
            try:
                r = self.post(url, body)
            except Exception as e:
                raise QiniuClientException(str(e))

        return _ret(r)

    def headers(self):
        return {'Authorization': 'UpToken {0}'.format(self.upToken), 'User-Agent': config.USER_AGENT}

    def post(self, url, data):
        return _post(url, data=data, headers=self.headers())
