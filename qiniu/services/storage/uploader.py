# -*- coding: utf-8 -*-

import os

import requests

from qiniu import consts
from qiniu.utils import base64Encode, crc32, localFileCrc32, _ret
from qiniu.exceptions import QiniuServiceException

_session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(max_retries=3)
_session.mount('http://', _adapter)


def put(upToken, key, data, params={}, mimeType='application/octet-stream', checkCrc=False):
    ''' put data to Qiniu
    If key is None, the server will generate one.
    data may be str or read()able object.
    '''
    crc = crc32(data) if checkCrc else None
    return _put(upToken, key, data, params, mimeType, crc)


def putFile(upToken, key, filePath, params={}, mimeType='application/octet-stream', checkCrc=False):
    ''' put data to Qiniu
    If key is None, the server will generate one.
    data may be str or read()able object.
    '''
    crc = localFileCrc32(filePath) if checkCrc else None
    return _put(upToken, key, open(filePath, 'rb'), params, mimeType, crc)


def _put(upToken, key, data, params, mimeType, crc32):
    fields = {}
    if params:
        for k, v in params.items():
            fields[k] = str(v)

    if crc32:
        fields['crc32'] = crc32

    if key is not None:
        fields['key'] = key

    fields['token'] = upToken

    url = 'http://' + consts.UP_HOST + '/'

    name = key if key else 'filename'

    r = _session.post(url, data=fields, files={'file': (name, data, mimeType)}, timeout=consts.DEFAULT_TIMEOUT)
    return _ret(r)


def resumablePut(upToken, key, reader, dataSize, params=None, mimeType=None):
    task = _Resume(upToken, key, reader, dataSize, params, mimeType)
    return task.upload()


def resumablePutFile(upToken, key, filePath, params=None, mimeType=None):
    ret = {}
    with open(filePath, 'rb') as reader:
        size = os.stat(filePath).st_size
        ret = resumablePut(upToken, key, reader, size, params, mimeType)
    return ret

_BLOCK_SIZE = 1024 * 1024 * 4


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

        return self.makeFile(consts.UP_HOST)

    def resumableBlockPut(self, upToken, block, length, index):
        if self.blockStatus[index] and 'ctx' in self.blockStatus[index]:
            return
        # todo retry
        self.blockStatus[index] = self.makeBlock(block, length)

        return

    def count(self):
        return (self.size + _BLOCK_SIZE - 1) // _BLOCK_SIZE

    def calcDataLengh(self, index):
        need = _BLOCK_SIZE
        if (index + 1) * _BLOCK_SIZE > self.size:
            need = self.size - index * _BLOCK_SIZE
        return need

    def makeBlock(self, block, blockSize):
        crc = crc32(block)
        block = bytearray(block)
        url = 'http://%s/mkblk/%s' % (consts.UP_HOST, blockSize)

        headers = self.headers()
        headers['Content-Type'] = 'application/octet-stream'

        r = _session.post(url, data=block, headers=headers, timeout=consts.DEFAULT_TIMEOUT)
        ret = _ret(r)
        if ret['crc32'] != crc:
            raise QiniuServiceException(r.status_code, 'unmatch crc checksum', r.headers['X-Reqid'])
        return ret

    def makeFileUrl(self, host):
        url = ['http://%s/mkfile/%s' % (host, self.size)]

        if self.mimeType:
            url.append('mimeType/%s' % base64Encode(self.mimeType))

        if self.key is not None:
            url.append('key/%s' % base64Encode(self.key))

        if self.params:
            for k, v in self.params.items():
                url.append('%s/%s' % (k, base64Encode(v)))

        url = '/'.join(url)
        return url

    def makeFile(self, host):
        url = self.makeFileUrl(host)
        body = ','.join([status['ctx'] for status in self.blockStatus])

        r = _session.post(url, data=body, headers=self.headers(), timeout=consts.DEFAULT_TIMEOUT)
        return _ret(r)

    def headers(self):
        return {'Authorization': 'UpToken %s' % self.upToken}
