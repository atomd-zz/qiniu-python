# -*- coding: utf-8 -*-


class QiniuServiceException(Exception):
    """common exception"""
    def __init__(self, statusCode, description, reqId):
        super(QiniuServiceException, self).__init__()
        self.statusCode = statusCode
        self.description = description
        self.reqId = reqId


class QiniuClientException(Exception):
    pass


class DeprecatedApi(QiniuClientException):
    """used deprecated api"""
