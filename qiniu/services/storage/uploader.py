# -*- coding: utf-8 -*-

import string

import requests

import qiniu.consts
from qiniu.auth import RequestsAuth

from qiniu.utils import base64Encode


def put(upToken, key, data, params={}, mimeType='application/octet-stream', crc32=None):
    """ put data to Qiniu
    If key is None, the server will generate one.
    data may be str or read()able object.
    """
    fields = {}

    if params:
        for k, v in params.items():
            fields[k] = str(v)

    if crc32:
        fields['crc32'] = crc32

    if key:
        fields['key'] = key

    fields['token'] = upToken

    # fname = key
    # if fname is None:
    #     fname = _random_str(9)
    # elif fname is '':
    #     fname = 'index.html'
    # undefined key ?

    url = 'http://' + qiniu.consts.UP_HOST + '/'

    # todo catch exception
    r = requests.post(url, data=fields, files={'file': (key, data, mimeType)})
    ret = r.json()
    err = None
    return ret, err


_TASK_QUEUE_SIZE = 4
_TRY_TIMES = 3

_BLOCK_SIZE = 1024*1024*4


err_put_failed = "resumable put failed"
err_unmatched_checksum = "unmatched checksum"


def resumablePut(upToken, key, data, dataSize, params={}, mimeType=None):
    task = _Resume(upToken, key, data, dataSize, params, mimeType)
    return task.upload()


class _Resume(object):

    def __init__(self, upToken, key, data, dataSize, params={}, mimeType=None):
        self.upToken = upToken
        self.key = key
        self.data = data
        self.dataSize = dataSize
        self.params = params
        self.mimeType = mimeType
        # self.notify = notify

    def upload(self):
        self.blockCount = self.count()
        self.blockStatus = [None] * blockCount

        # todo cactch exception
        for i in xrange(blockCount):
            length = self.calcDataLengh(i)
            dataBlock = f.read(readLength)

            err = self.resumableBlockPut(upToken, dataBlock, length,  i)
            if err is not None:
                return None, err_put_failed, 0

        return self.makeFile()

    def resumableBlockPut(self, upToken, block, length, index):
        if self.blockStatus[index] and "ctx" in self.blockStatus[index]:
            return
        # todo retry
        self.blockStatus[index] = self.makeBlock(block, length)
        # todo notify
        # if self.notify:
        #     self.notify(index, block_size, self.blockStatus[index])
        return

    def blockCount(self):
        return (self.size + _BLOCK_SIZE - 1) / _BLOCK_SIZE

    def calcDataLengh(self, index):
        need = _BLOCK_SIZE
        if (index + 1) * _BLOCK_SIZE > self.size:
            need = self.size - index * _BLOCK_SIZE
        return need

    def makeBlock(self, block, blockSize):
        crc = crc32(block)
        block = bytearray(block)
        url = "http://%s/mkblk/%s" % (host, blockSize)
        content_type = "application/octet-stream"

        ret = client.call_with(url, first_chunk, content_type, len(first_chunk))
        if not ret['crc32'] == crc:
            raise err_unmatched_checksum
        return ret

    def makeFileUrl(self, host):
        url = ["http://%s/mkfile/%s" % (host, self.size)]

        if self.mimeType:
            url.append("mimeType/%s" % base64Encode(self.mimeType))

        if key is not None:
            url.append("key/%s" % base64Encode(key))

        if self.params:
            for k, v in self.params.iteritems():
                url.append("%s/%s" % (k, base64Encode(v)))

        url = "/".join(url)
        return url

    def makeFile(self, host):
        url = self.makeFileUrl(host)
        body = ",".join([status["ctx"] for status in self.blockStatus])
        return client.call_with(url, body, "text/plain", len(body))
