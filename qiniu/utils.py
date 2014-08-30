from . import __version__
import platform

sys_info = "%s/%s" % (platform.system(), platform.machine())
py_ver = platform.python_version()

USER_AGENT = "QiniuPython/%s (%s) Python/%s" % (__version__, sys_info, py_ver)
