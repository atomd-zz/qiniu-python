import requests

from qiniu import config
from qiniu.auth import RequestsAuth

from qiniu.utils import _ret, entry


def pfop(auth, bucket, key, fops, pipeline=None, notify_url=None):
    ops = '|'.join(fops)
    data = {'bucket': bucket, 'key': key, 'fops': ops}
    if pipeline:
        data['pipeline'] = pipeline
    if notify_url:
        data['notifyURL'] = notify_url

    headers = {'User-Agent': config.USER_AGENT}

    url = 'http://{0}/pfop'.format(config.API_HOST)

    r = requests.post(
        url, data=data, auth=RequestsAuth(auth),
        timeout=config.get_default('connection_timeout'), headers=headers)
    return _ret(r)


def op_saveas(bucket, key):
    return 'saveas/{0}'.format(entry(bucket, key))
