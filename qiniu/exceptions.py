# -*- coding: utf-8 -*-


class QiniuException(IOError):
    """common exception"""
    def __init__(self, statusCode, description, reqId):
        super(QiniuException, self).__init__()
        self.statusCode = statusCode
        self.description = description
        self.reqId = reqId


class DeprecatedApi(ValueError):
    """used deprecated api"""
