from oauth_base import *
import urllib, urllib2
from logging import warning as w_log
import web

class DoubanOauth(OauthBase):
    def __init__(self):
        super(DoubanOauth, self).__init__(DB_APP_KEY, DB_APP_SECRET, 'douban', SERVER_ADDR[OAUTH_DEF['douban']], DB_CALLBACK)
    def getAuthorizeURL(self):
        print DB_CALLBACK
        url_str = self.oauth_server_addr + ('?client_id=%s' % self.app_key) + \
                  ('&redirect_uri=%s' % self.callback) + \
                  ('&response_type=code&scope=douban_basic_common')
        print url_str
        return url_str
    def saveAuthorizeInfo(self):
        pass

if __name__ == "__main__":
    dou = DoubanOauth()
    print dou.getAuthorizeURL()
