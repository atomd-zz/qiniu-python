# -*- coding: utf-8 -*-

import os

import requests

from qiniu import config
from qiniu.utils import base64Encode, crc32, localFileCrc32, _ret
from qiniu.exceptions import QiniuServiceException, QiniuClientException


_session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(
    pool_connections=config._connectionPool, pool_maxsize=config._connectionPool,
    max_retries=config._connectionRetries)
_session.mount('http://', _adapter)


def _needRetry(response, exception):
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


def putFile(
        upToken, key, filePath, params=None, mimeType='application/octet-stream', checkCrc=False):
    ''' put data to Qiniu
    If key is None, the server will generate one.
    data may be str or read()able object.
    '''
    crc = localFileCrc32(filePath) if checkCrc else None
    with open(filePath, 'rb') as reader:
            return _put(upToken, key, reader, params, mimeType, crc)


def _put(upToken, key, data, params, mimeType, crc32, filePath=None):
    fields = {}
    if params:
        for k, v in params.items():
            fields[k] = str(v)

    if crc32:
        fields['crc32'] = crc32

    if key is not None:
        fields['key'] = key

    fields['token'] = upToken

    url = 'http://' + config._defaultUpHost + '/'

    name = key if key else 'filename'

    r = None
    exception = None
    try:
        r = _session.post(
            url, data=fields, files={'file': (name, data, mimeType)},
            timeout=config._connectionTimeout)
    except Exception as e:
        exception = e
    finally:
        retry = _needRetry(r, exception)

    if retry:
        url = 'http://' + config.UPBACKUP_HOST + '/'
        if filePath:
            data.seek(0)
        try:
            r = _session.post(
                url, data=fields, files={'file': (name, data, mimeType)},

                timeout=config._connectionTimeout)
        except Exception as e:
            raise QiniuClientException(str(e))

    return _ret(r)


def resumablePut(upToken, key, reader, dataSize, params=None, mimeType=None):
    task = _Resume(upToken, key, reader, dataSize, params, mimeType)
    return task.upload()


def resumablePutFile(upToken, key, filePath, params=None, mimeType=None):
    ret = {}
    size = os.stat(filePath).st_size
    with open(filePath, 'rb') as reader:
        ret = resumablePut(upToken, key, reader, size, params, mimeType)
    return ret


class _Resume(object):

    def __init__(self, upToken, key, reader, dataSize, params, mimeType):
        self.upToken = upToken
        self.key = key
        self.reader = reader
        self.size = dataSize
        self.params = params
        self.mimeType = mimeType
        # self.notify = notify

    def upload(self):
        self.blockCount = self.count()
        self.blockStatus = [None] * self.blockCount

        # todo cactch exception
        for i in range(self.blockCount):
            length = self.calcDataLengh(i)
            dataBlock = self.reader.read(length)

            self.resumableBlockPut(self.upToken, dataBlock, length,  i)

        return self.makeFile()

    def resumableBlockPut(self, upToken, block, length, index):
        if self.blockStatus[index] and 'ctx' in self.blockStatus[index]:
            return
        # todo retry
        self.blockStatus[index] = self.makeBlock(block, length)

        return

    def count(self):
        return (self.size + config._BLOCK_SIZE - 1) // config._BLOCK_SIZE

    def calcDataLengh(self, index):
        need = config._BLOCK_SIZE
        if (index + 1) * config._BLOCK_SIZE > self.size:
            need = self.size - index * config._BLOCK_SIZE
        return need

    def makeBlock(self, block, blockSize):
        crc = crc32(block)
        block = bytearray(block)
        url = self.blockUrl(config._defaultUpHost, blockSize)
        headers = self.headers()
        headers['Content-Type'] = 'application/octet-stream'

        r = None
        exception = None
        try:
            r = _session.post(url, data=block, headers=headers, timeout=config._connectionTimeout)
        except Exception as e:
            exception = e
        finally:
            retry = _needRetry(r, exception)

        if retry:
            url = self.blockUrl(config.UPBACKUP_HOST, blockSize)
            try:
                r = _session.post(url, data=block, headers=headers, timeout=config._connectionTimeout)
            except Exception as e:
                raise QiniuClientException(str(e))

        ret = _ret(r)
        if ret['crc32'] != crc:
            raise QiniuServiceException(
                r.status_code, 'unmatch crc checksum', r.headers['X-Reqid'])
        return ret

    def blockUrl(self, host, size):
        return 'http://%s/mkblk/%s'.format(host, size)

    def makeFileUrl(self, host):
        url = ['http://%s/mkfile/%s'.format(host, self.size)]

        if self.mimeType:
            url.append('mimeType/%s'.format(base64Encode(self.mimeType)))

        if self.key is not None:
            url.append('key/%s'.format(base64Encode(self.key)))

        if self.params:
            for k, v in self.params.items():
                url.append('%s/%s'.format(k, base64Encode(v)))

        url = '/'.join(url)
        return url

    def makeFile(self):
        url = self.makeFileUrl(config._defaultUpHost)
        body = ','.join([status['ctx'] for status in self.blockStatus])

        r = None
        exception = None
        try:
            r = _session.post(
                url, data=body, headers=self.headers(), timeout=config._connectionTimeout)
        except Exception as e:
            exception = e
        finally:
            retry = _needRetry(r, exception)

        if retry:
            url = self.makeFileUrl(config._defaultUpHost)
            try:
                r = _session.post(
                    url, data=body, headers=self.headers(), timeout=config._connectionTimeout)
            except Exception as e:
                raise QiniuClientException(str(e))

        r = _session.post(
            url, data=body, headers=self.headers(), timeout=config._connectionTimeout)
        return _ret(r)

    def headers(self):
        return {'Authorization': 'UpToken %s'.format(self.upToken)}
