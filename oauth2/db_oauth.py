#!/usr/bin/env python
#! -*- coding:utf-8 -*-
from oauth_base import *

class DoubanOauth(OauthBase):
    def __init__(self, profile_id = 0):
        super(DoubanOauth, self).__init__(DB_APP_KEY, DB_APP_SECRET, 'douban', SERVER_ADDR[OAUTH_DEF['douban']], DB_CALLBACK)
        #profile_id 为0表示新用户注册
        self.profile_id = profile_id
    def redirectToAuth(self):
        self.logger.warning("db_auth redirect, profile_id:%s" % self.profile_id)
        url_str = self.oauth_server_addr + ('?client_id=%s' % self.app_key) + \
                  ('&redirect_uri=%s' % self.callback) + \
                  ('&response_type=code&scope=douban_basic_common&state=%s' % self.profile_id)
        raise web.seeother(url_str)
    def authCallback(self):
        getdata     = web.input()
        code        = getdata.get('code')
        state       = getdata.get('state')
        post_url = DB_OAUTH_URL + '/token'
        ret = self.makePostReq(post_url, code = code, client_id = DB_APP_KEY,
                               client_secret = DB_APP_SECRET, redirect_uri = DB_CALLBACK,
                               grant_type = 'authorization_code')
        if ret is None:
            #请求失败
            raise web.seeother('fault.html')
        ret_dict = eval(ret)

        oauth_access_token      = ret_dict['access_token']
        oauth_expires           = ret_dict['expires_in']
        server_user_id          = ret_dict['douban_user_id']
        #这里数据库中的oauth_ser_user_id字段需要加上来自哪个平台的前缀, 以保证在整张表中的唯一性 
        oauth_server_user_id    = ('douban-%s' % server_user_id) 
        oauth_c = model.OauthClass()
        oauth_id, oauth_profile_id = oauth_c.getBindUserId(oauth_server_user_id)

        profile_id = int(state)

        if (not oauth_id is None) and (not oauth_profile_id is None):
            #该账号已经被绑定过了, 如果此时用户还没有登录, 那么用户是要登录
            if profile_id == 0:
                session = web.config._session
                session.profile_id  = oauth_profile_id
                session.login       = True
                raise web.seeother('/welcome')
            else:
            #该账号已经绑定, 但是用户已经登录本地账号, 还试图将这个账号绑定到已经登录的本地账号上, 则认为是错误的
                raise web.seeother('fault.html')

        return profile_id, oauth_access_token, oauth_expires, oauth_server_user_id

    def saveAuthorizeInfo(self):
        pass

if __name__ == "__main__":
    dou = DoubanOauth('new_bind')
    print dou.redirectToAuth()
