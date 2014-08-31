# -*- coding: utf-8 -*-

import string
try:
    import zlib
    binascii = zlib
except ImportError:
    zlib = None
    import binascii

import requests

import qiniu.consts
from qiniu.auth import RequestsAuth


def put(uptoken, key, data, params={}, mime_type='application/octet-stream', checkCrc=0,  crc32=''):
    """ put your data to Qiniu

    If key is None, the server will generate one.
    data may be str or read()able object.
    """
    fields = {}

    if params:
        for k, v in params.items():
            fields[k] = str(v)

    if checkCrc:
        fields['crc32'] = str(crc32)

    if key is not None:
        fields['key'] = key

    fields['token'] = uptoken

    # fname = key
    # if fname is None:
    #     fname = _random_str(9)
    # elif fname is '':
    #     fname = 'index.html'
    # undefined key ?

    # fields['file'] = (key, data, mime_type)
    url = 'http://' + qiniu.consts.UP_HOST + '/'

    r = requests.post(url, data=fields, files={'file': (key, data, mime_type)})
    ret = r.json()
    err = None
    return ret, err


def putFile(uptoken, key, localfile, params={}, mimeType='application/octet-stream', checkCrc=0,  crc32=''):
    """ put a file to Qiniu

    If key is None, the server will generate one.
    """
    if checkCrc == 1:
        crc32 = _get_file_crc32(localfile)
    with open(localfile, 'rb') as f:
        return put(uptoken, key, f, params, mimeType, checkCrc, crc32)


_BLOCK_SIZE = 1024 * 1024 * 4


def _get_file_crc32(filepath):
    with open(filepath, 'rb') as f:
        block = f.read(_BLOCK_SIZE)
        crc = 0
        while len(block) != 0:
            crc = binascii.crc32(block, crc) & 0xFFFFFFFF
            block = f.read(_BLOCK_SIZE)
    return crc


_workers = 1
_task_queue_size = _workers * 4
_try_times = 3
_block_bits = 22
_block_size = 1 << _block_bits
_block_mask = _block_size - 1
_chunk_size = _block_size  # 简化模式，弃用


class ResumableIoError(object):
    value = None

    def __init__(self, value):
        self.value = value
        return

    def __str__(self):
        return self.value


err_invalid_put_progress = ResumableIoError("invalid put progress")
err_put_failed = ResumableIoError("resumable put failed")
err_unmatched_checksum = ResumableIoError("unmatched checksum")
err_putExtra_type = ResumableIoError("extra must the instance of PutExtra")


def setup(chunk_size=0, try_times=0):
    global _chunk_size, _try_times
    _chunk_size = 1 << 22 if chunk_size <= 0 else chunk_size
    _try_times = 3 if try_times == 0 else try_times
    return


def gen_crc32(data):
    return binascii.crc32(data) & 0xffffffff


class PutExtra(object):
    params = None          # 自定义用户变量, key需要x: 开头
    mimetype = None        # 可选。在 uptoken 没有指定 DetectMime 时，用户客户端可自己指定 MimeType
    chunk_size = None      # 可选。每次上传的Chunk大小 简化模式，弃用
    try_times = None       # 可选。尝试次数
    progresses = None      # 可选。上传进度
    notify = lambda self, idx, size, ret: None  # 可选。进度提示
    notify_err = lambda self, idx, size, err: None

    def __init__(self, bucket=None):
        self.bucket = bucket
        return


def resumablePutFile(uptoken, key, localfile, extra):
    """ 上传文件 """
    f = open(localfile, "rb")
    statinfo = os.stat(localfile)
    ret, err = put(uptoken, key, f, statinfo.st_size, extra)
    f.close()
    return ret, err


def resumablePut(uptoken, key, f, fsize, extra):
    """ 上传二进制流, 通过将data "切片" 分段上传 """
    if not isinstance(extra, PutExtra):
        print("extra must the instance of PutExtra")
        return
    host = conf.UP_HOST
    try:
        ret, err, code = put_with_host(uptoken, key, f, fsize, extra, host)
        if err is None or code / 100 == 4 or code == 579 or code / 100 == 6 or code / 100 == 7:
            return ret, err
    except:
        pass

    ret, err, code = put_with_host(uptoken, key, f, fsize, extra, conf.UP_HOST2)
    return ret, err


def put_with_host(uptoken, key, f, fsize, extra, host):
    block_cnt = block_count(fsize)
    if extra.progresses is None:
        extra.progresses = [None] * block_cnt
    else:
        if not len(extra.progresses) == block_cnt:
            return None, err_invalid_put_progress, 0

    if extra.try_times is None:
        extra.try_times = _try_times

    if extra.chunk_size is None:
        extra.chunk_size = _chunk_size

    for i in xrange(block_cnt):
        try_time = extra.try_times
        read_length = _block_size
        if (i + 1) * _block_size > fsize:
            read_length = fsize - i * _block_size
        data_slice = f.read(read_length)
        while True:
            err = resumable_block_put(data_slice, i, extra, uptoken, host)
            if err is None:
                break

            try_time -= 1
            if try_time <= 0:
                return None, err_put_failed, 0
            print err, ".. retry"

    mkfile_host = extra.progresses[-1]["host"] if block_cnt else host
    mkfile_client = auth_up.Client(uptoken, mkfile_host)

    return mkfile(mkfile_client, key, fsize, extra, host)


def resumable_block_put(block, index, extra, uptoken, host):
    block_size = len(block)

    mkblk_client = auth_up.Client(uptoken, host)
    if extra.progresses[index] is None or "ctx" not in extra.progresses[index]:
        crc32 = gen_crc32(block)
        block = bytearray(block)
        extra.progresses[index], err, code = mkblock(mkblk_client, block_size, block, host)
        if err is not None:
            extra.notify_err(index, block_size, err)
            return err
        if not extra.progresses[index]["crc32"] == crc32:
            return err_unmatched_checksum
        extra.notify(index, block_size, extra.progresses[index])
        return


def block_count(size):
    global _block_size
    return (size + _block_mask) / _block_size


def mkblock(client, block_size, first_chunk, host):
    url = "http://%s/mkblk/%s" % (host, block_size)
    content_type = "application/octet-stream"
    return client.call_with(url, first_chunk, content_type, len(first_chunk))


def putblock(client, block_ret, chunk):
    url = "%s/bput/%s/%s" % (block_ret["host"],
                             block_ret["ctx"], block_ret["offset"])
    content_type = "application/octet-stream"
    return client.call_with(url, chunk, content_type, len(chunk))


def mkfile(client, key, fsize, extra, host):
    url = ["http://%s/mkfile/%s" % (host, fsize)]

    if extra.mimetype:
        url.append("mimeType/%s" % urlsafe_b64encode(extra.mimetype))

    if key is not None:
        url.append("key/%s" % urlsafe_b64encode(key))

    if extra.params:
        for k, v in extra.params.iteritems():
            url.append("%s/%s" % (k, urlsafe_b64encode(v)))

    url = "/".join(url)
    body = ",".join([i["ctx"] for i in extra.progresses])
    return client.call_with(url, body, "text/plain", len(body))
