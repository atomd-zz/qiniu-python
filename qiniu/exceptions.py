# -*- coding: utf-8 -*-


class QiniuServiceException(Exception):
    """common exception"""
    def __init__(self, statusCode, description, reqId):
        super(QiniuServiceException, self).__init__()
        self.statusCode = statusCode
        self.description = description
        self.reqId = reqId


class QiniuClientException(Exception):
    def __init__(self, message):
        self.message = message
        super(QiniuClientException, self).__init__(message)


class DeprecatedApi(QiniuClientException):
    def __init__(self, api):
        self.message = api + ' has deprecated'
        super(QiniuClientException, self).__init__(self.message)
