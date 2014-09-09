# -*- coding: utf-8 -*-

import os
import platform
from hashlib import sha1
from base64 import urlsafe_b64encode

from .config import _BLOCK_SIZE

try:
    import zlib
    binascii = zlib
except ImportError:
    zlib = None
    import binascii

from .exceptions import QiniuServiceException
from . import __version__

import sys

_ver = sys.version_info
is_py2 = (_ver[0] == 2)


def base64Encode(data):
    if not is_py2:
        if isinstance(data, str):
            data = bytes(data, 'utf-8')
    ret = urlsafe_b64encode(data)
    if not is_py2:
        if isinstance(data, bytes):
            ret = ret.decode('utf-8')
    return ret


def localFileCrc32(filePath):
    crc = 0
    with open(filePath, 'rb') as f:
        for block in _fileIter(f, _BLOCK_SIZE):
            crc = binascii.crc32(block, crc) & 0xFFFFFFFF
    return crc


def crc32(data):
    if not is_py2:
        if isinstance(data, str):
            data = bytes(data, 'utf-8')
    return binascii.crc32(data) & 0xffffffff


def _ret(req):
    ret = req.json() if req.text != '' else {}
    if req.status_code//100 != 2:
        reqId = req.headers['X-Reqid']
        raise QiniuServiceException(req.status_code, ret['error'], reqId)
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


if is_py2:
    _hashPrefix = ['\x16', '\x96']
else:
    _hashPrefix = [bytes.fromhex('16'), bytes.fromhex('96')]


def _hashEncode(array):
    data = None
    prefix = None
    if len(array) == 1:
        data = array[0]
        prefix = _hashPrefix[0]
    else:
        if is_py2:
            s = ''.join(array)
        else:
            s = b''.join(array)
        data = _sha1(s)
        prefix = _hashPrefix[1]
    return base64Encode(prefix + data)


def _etag(inputStream):
    l = [_sha1(block) for block in _fileIter(inputStream, 4 * 1024 * 1024)]
    return _hashEncode(l)


def etag(filePath):
    size = os.stat(filePath).st_size
    if size == 0:
        return base64Encode('\x16')
    with open(filePath, 'rb') as f:
        return _etag(f)
