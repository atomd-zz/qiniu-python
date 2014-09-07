# -*- coding: utf-8 -*-

RS_HOST = 'rs.qbox.me'
IO_HOST = 'iovip.qbox.me'
RSF_HOST = 'rsf.qbox.me'

UPAUTO_HOST = 'up.qiniu.com'
UPDX_HOST = 'updx.qiniu.com'
UPLT_HOST = 'uplt.qiniu.com'
UPBACKUP_HOST = 'upload.qiniu.com'

_config = {
    'defaultUpHost': UPAUTO_HOST,
    'connectionTimeout': 30,
    'connectionRetries': 3,
    'connectionPool': 10,

}
_BLOCK_SIZE = 1024 * 1024 * 4


def getDefault(key):
    return _config[key]


def setDefault(
        defaultUpHost=None, connectionRetries=None, connectionPool=None, connectionTimeout=None):
    if defaultUpHost:
        _config['defaultUpHost'] = defaultUpHost
    if connectionRetries:
        _config['connectionRetries'] = connectionRetries
    if connectionPool:
        _config['connectionPool'] = connectionPool
    if connectionTimeout:
        _config['connectionTimeout'] = connectionTimeout
