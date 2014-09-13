# -*- coding: utf-8 -*-

from hashlib import sha1
from base64 import urlsafe_b64encode

from .config import _BLOCK_SIZE

from .compat import b, s

try:
    import zlib
    binascii = zlib
except ImportError:
    zlib = None
    import binascii

from .exceptions import QiniuServiceException


def base64Encode(data):
    ret = urlsafe_b64encode(b(data))
    return s(ret)


def localFileCrc32(filePath):
    crc = 0
    with open(filePath, 'rb') as f:
        for block in _fileIter(f, _BLOCK_SIZE):
            crc = binascii.crc32(block, crc) & 0xFFFFFFFF
    return crc


def crc32(data):
    return binascii.crc32(b(data)) & 0xffffffff


def _ret(resp):
    ret = resp.json() if resp.text != '' else {}
    if resp.status_code//100 != 2:
        reqId = resp.headers['X-Reqid']
        raise QiniuServiceException(resp.status_code, ret['error'], reqId)
    return ret


def _fileIter(inputStream, size):
    d = inputStream.read(size)
    while d:
        yield d
        d = inputStream.read(size)


def _sha1(data):
    h = sha1()
    h.update(data)
    return h.digest()


def _hashEncode(array):
    if len(array) == 1:
        data = array[0]
        prefix = b('\x16')
    else:
        s = b('').join(array)
        data = _sha1(s)
        prefix = b('\x96')
    return base64Encode(prefix + data)


def _etag(inputStream):
    l = [_sha1(block) for block in _fileIter(inputStream, _BLOCK_SIZE)]
    return _hashEncode(l)


def etag(filePath):
    with open(filePath, 'rb') as f:
        return _etag(f)
