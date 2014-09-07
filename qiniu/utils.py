#! /usr/bin/env python
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

from requests.compat import is_py2

from .exceptions import QiniuServiceException
from . import __version__


sys_info = '%s; %s'.format(platform.system(), platform.machine())
py_ver = platform.python_version()

USER_AGENT = 'QiniuPython/%s (%s; ) Python/%s'.format(__version__, sys_info, py_ver)


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
        block = f.read(_BLOCK_SIZE)
        while len(block) != 0:
            crc = binascii.crc32(block, crc) & 0xFFFFFFFF
            block = f.read(_BLOCK_SIZE)
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


def etag(filePath):
    size = os.stat(filePath).st_size
    if size == 0:
        return ''
