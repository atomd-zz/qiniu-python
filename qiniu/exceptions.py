# -*- coding: utf-8 -*-


class QiniuServiceException(Exception):
    """common exception"""
    def __init__(self, status_code, description, req_id):
        super(QiniuServiceException, self).__init__()
        self.status_code = status_code
        self.description = description
        self.req_id = req_id


class QiniuClientException(Exception):
    def __init__(self, message):
        self.message = message
        super(QiniuClientException, self).__init__(message)


class DeprecatedApi(QiniuClientException):
    def __init__(self, api):
        self.message = api + ' has deprecated'
        super(QiniuClientException, self).__init__(self.message)
