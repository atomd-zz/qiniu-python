# -*- coding: utf-8 -*-


class QiniuException(IOError):
    """common exception"""
    def __init__(self, arg):
        super(QiniuException, self).__init__()
        self.arg = arg


class DeprecatedApi(QiniuException):
    """used deprecated api"""
