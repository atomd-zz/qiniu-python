# -*- coding: utf-8 -*-

RS_HOST = 'rs.qbox.me'
IO_HOST = 'iovip.qbox.me'
RSF_HOST = 'rsf.qbox.me'

UPAUTO_HOST = 'up.qiniu.com'
UPDX_HOST = 'updx.qiniu.com'
UPLT_HOST = 'uplt.qiniu.com'
UPBACKUP_HOST = 'upload.qiniu.com'

_defaultUpHost = UPAUTO_HOST

_connectionTimeout = 30
_connectionRetries = 3
_connectionPool = 10

_BLOCK_SIZE = 1024 * 1024 * 4


def setDefault(
        defaultUpHost=None, connectionRetries=None, connectionPool=None, connectionTimeout=None):
    if defaultUpHost:
        _defaultUpHost = defaultUpHost
    if connectionRetries:
        _connectionRetries = connectionRetries
    if connectionPool:
        _connectionPool = connectionPool
    if connectionTimeout:
        _connectionTimeout = connectionTimeout
