# -*- coding: utf-8 -*-

from . import __version__
import platform

from base64 import urlsafe_b64encode

try:
    import zlib
    binascii = zlib
except ImportError:
    zlib = None
    import binascii

from requests.compat import is_py2

sys_info = "%s; %s" % (platform.system(), platform.machine())
py_ver = platform.python_version()

USER_AGENT = "QiniuPython/%s (%s; ) Python/%s" % (__version__, sys_info, py_ver)


def base64Encode(data):
    if not is_py2:
        if isinstance(data, str):
            data = bytes(data, 'utf-8')
    ret = urlsafe_b64encode(data)
    if not is_py2:
        if isinstance(data, bytes):
            ret = ret.decode('utf-8')
    return ret

_BLOCK_SIZE = 1024 * 1024 * 4


def fileCrc32(filePath):
    with open(filePath, 'rb') as f:
        block = f.read(_BLOCK_SIZE)
        crc = 0
        while len(block) != 0:
            crc = binascii.crc32(block, crc) & 0xFFFFFFFF
            block = f.read(_BLOCK_SIZE)
    return crc


def crc32(data):
    if not is_py2:
        if isinstance(data, str):
            data = bytes(data, 'utf-8')
    return binascii.crc32(data) & 0xffffffff
