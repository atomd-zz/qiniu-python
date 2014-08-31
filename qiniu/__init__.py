# -*- coding: utf-8 -*-
'''
Qiniu Resource Storage SDK for Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For detailed document, please see:
<http://developer.qiniu.com>
'''

__version__ = '7.0.0'

from .auth import Auth

from .exceptions import DeprecatedApi

from .services.storage.bucket import Bucket
from .services.storage.uploader import Uploader
