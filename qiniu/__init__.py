# -*- coding: utf-8 -*-
'''
Qiniu Resource Storage SDK for Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For detailed document, please see:
<http://developer.qiniu.com>
'''

# flake8: noqa

__version__ = '7.0.0'

from .auth import Auth

from .exceptions import DeprecatedApi, QiniuServiceException
from .config import set_default

from .services.storage.bucket import Bucket
from .services.storage.uploader import put, putfile, resumable_put, resumable_putfile
from .services.processing.media import pfop

from .utils import urlsafe_base64_encode, urlsafe_base64_decode, etag, entry
