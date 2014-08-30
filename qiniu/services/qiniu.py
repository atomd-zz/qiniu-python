RS_HOST = "rs.qiniu.com"
RSF_HOST = "rsf.qiniu.com"
UP_HOST = "up.qiniu.com"
UP_HOST2 = "upload.qiniu.com"
DEFAULT_TIMEOUT= 30

class Qiniu(object):
    def __init__(self, accessKey, secretKey):
        self.auth = Auth(accessKey, secretKey)

    def bucket(self, name):
        return Bucket(name, self.auth)

    def buckets(self):
        pass

    def downloadToken(self, baseUrl, expires=3600):
        '''
         *  return private url
        '''

        deadline = int(time.time()) + expires
        if '?' in baseUrl:
            baseUrl += '&'
        else:
            baseUrl += '?'
        baseUrl = '%se=%s' % (baseUrl, str(deadline))

        token = auth.token(baseUrl)
        return '%s&token=%s' % (baseUrl, token)

    def uploadToken(self, scope, policy=None, expires=3600):
        pass
