# -*- coding: utf-8 -*-

import string

import requests

from qiniu import consts
from qiniu.auth import RequestsAuth

from qiniu.utils import base64Encode, crc32


def put(upToken, key, data, params={}, mimeType='application/octet-stream', crc32=None):
    ''' put data to Qiniu
    If key is None, the server will generate one.
    data may be str or read()able object.
    '''
    fields = {}

    if params:
        for k, v in params.items():
            fields[k] = str(v)

    if crc32:
        fields['crc32'] = crc32

    if key:
        fields['key'] = key
    else:
        fields['key'] = ''

    fields['token'] = upToken

    url = 'http://' + consts.UP_HOST + '/'

    # todo no key specify
    name = key if key else 'filename'

    r = requests.post(url, data=fields, files={'file': (name, data, mimeType)})
    ret = r.json()
    err = None
    return ret, err


_TASK_QUEUE_SIZE = 4
_TRY_TIMES = 3

_BLOCK_SIZE = 1024*1024*4

err_unmatched_checksum = 'unmatched checksum'


def resumablePut(upToken, key, reader, dataSize, params=None, mimeType=None):
    task = _Resume(upToken, key, reader, dataSize, params, mimeType)
    return task.upload()


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

            err = self.resumableBlockPut(self.upToken, dataBlock, length,  i)
            if err is not None:
                return None, err, 0

        return self.makeFile(consts.UP_HOST)

    def resumableBlockPut(self, upToken, block, length, index):
        if self.blockStatus[index] and 'ctx' in self.blockStatus[index]:
            return
        # todo retry
        self.blockStatus[index] = self.makeBlock(block, length)
        # todo notify
        # if self.notify:
        #     self.notify(index, block_size, self.blockStatus[index])
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

        r = requests.post(url, data=block, headers=headers)
        ret = r.json()
        if not ret['crc32'] == crc:
            raise err_unmatched_checksum
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

        r = requests.post(url, data=body, headers=self.headers())
        ret = r.json()
        return ret, None

    def headers(self):
        return {'Authorization': 'UpToken %s' % self.upToken}
