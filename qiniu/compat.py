# -*- coding: utf-8 -*-

"""
pythoncompat
"""

import sys

try:
    import simplejson as json
except (ImportError, SyntaxError):
    # simplejson does not support Python 3.2, it thows a SyntaxError
    # because of u'...' Unicode literals.
    import json


# -------
# Pythons
# -------

_ver = sys.version_info

#: Python 2.x?
is_py2 = (_ver[0] == 2)

#: Python 3.x?
is_py3 = (_ver[0] == 3)


# ---------
# Specifics
# ---------

if is_py2:
    from urlparse import urlparse
    import StringIO
    StringIO = BytesIO = StringIO.StringIO

    builtin_str = str
    bytes = str
    str = unicode
    basestring = basestring
    numeric_types = (int, long, float)

    def b(s):
        return s

    def u(s):
        return unicode(s, 'unicode_escape')

elif is_py3:
    from urllib.parse import urlparse
    import io
    StringIO = io.StringIO
    BytesIO = io.BytesIO

    builtin_str = str
    str = str
    bytes = bytes
    basestring = (str, bytes)
    numeric_types = (int, float)

    def b(s):
        return s.encode('utf-8')

    def u(s):
        return s
