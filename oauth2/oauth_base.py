import os
import sys
sys.path.append('/home/pi/source/xcf')

from conf import *
import model

OAUTH_DEF = {'douban': 0, 'weibo': 1, 'qqzone': 2}
OAUTH_FROM = ['douban', 'weibo', 'qqzone',]
SERVER_ADDR = ['https://www.douban.com/service/auth2/auth',
               'https://tobedone',
               'https://tobedone',]

class OauthBase(object):
    def __init__(self, app_key, app_secret, oauth_from, oauth_server_addr, callback):
        self.app_key = app_key
        self.app_secret = app_secret
        self.oauth_from = oauth_from
        self.oauth_server_addr = oauth_server_addr
        self.callback = callback
    def __del__(self):
        pass
    def makePostReq(self, base_url, **kwargs):
        req = urllib2.Request(base_url, data=urllib.urlencode(kwargs))
        try:
            page = urllib2.urlopen(req)
            return eval(page.read(-1))
        except urllib2.HTTPError, e:
            print "Error Code:", e.code
        except urllib2.URLError, e:
            print "Error Reason", e.reason
        return None
    def getAuthorizeURL(self):
        pass
    def saveAuthorizeInfo(self):
        pass

