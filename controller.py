#!/usr/bin/env python
#! -*- coding:utf-8 -*-
import urllib, urllib2
from logging import warning as w_log
import web
import pprint
from mako.template import Template
from conf import *
import model
from oauth2 import *
from conf.oauth_setting import *
from socialoauth import SocialSites, SocialAPIError
#from socialoauth import SoicalSites

class statics(object):
    def GET(self, file_name, content_type):
        file_path = PATH_STATICS + '/' + file_name
        print file_path
        web.header('Content-Type', content_type)
        with open(file_path) as f:
            return f.read(-1)

class cssStatics(statics):
    def GET(self, file_name):
        return statics.GET(self, file_name, 'text/css')

class jsStatics(statics):
    def GET(self, file_name):
        return statics.GET(self, file_name, 'application/x-javascript')

class index:
    def GET(self):
        tt = Template(filename = './template/index.html')
        return tt.render()
    POST = GET

class login:
    def GET(self):
        raise web.seeother('/')
    def POST(self):
        postdata = web.input()
        profile_id = int(postdata.get('profile_id'))
        local_auth_password = postdata.get('local_auth_password')
        local_auth_c = model.LocalAuthClass()
        if local_auth_c.verifyLocalAuth(profile_id, local_auth_password) == False:
            return '用户名或密码错误, 请退回重试'
        else:
            #login success
            profile = model.Profile(profile_id)
            session = web.config._session
            session.login = True
            session.username = profile.profile_username
            session.welcome = profile.profile_welcome
            session.profile_id = profile.profile_id
            raise web.seeother('/welcome')
class welcome:
    def GET(self):
        session = web.config._session
        if not session.login:
            return '请登录后重试'
        if session.profile_id == 0:
            return '请登录后重试'
        else:
            tt = Template(filename = './template/welcome.html')
            profile_id = session.profile_id
            profile = model.Profile(profile_id)
            session.username = profile.profile_username
            session.welcome = profile.profile_welcome
            session.bind_cnt = profile.profile_bind_cnt
            return tt.render(profile_username = session.username, profile_welcome = session.welcome,
                             profile_id = session.profile_id)
    POST = GET

class signup:
    def GET(self):
        tt = Template(filename = './template/signup.html')
        return tt.render()
    def POST(self):
        postdata = web.input()
        profile_username = postdata.get('profile_username').encode('utf-8')
        profile_welcome = postdata.get('profile_welcome').encode('utf-8')
        local_auth_password = postdata.get('local_auth_password')
        profile_c = model.ProfileClass()
        profile_id = profile_c.addProfile(1, profile_username, profile_welcome)

        local_auth_c = model.LocalAuthClass()
        local_auth_c.addLocalAuth(profile_id, local_auth_password)

        return '注册成功, 您的用户名: %s 用户ID: %d, 请保存好用户ID, 凭ID登陆' % (profile_username, profile_id)

class modify:
    def GET(self):
        session = web.config._session
        if not session.login:
            return '请登录后重试'
        profile_id = session.profile_id
        profile_username = session.username
        profile_welcome = session.welcome

        tt = Template(filename = './template/modify.html')
        return tt.render(profile_id = profile_id, profile_username = profile_username,
                         profile_welcome = profile_welcome)
    def POST(self):
        session = web.config._session
        if not session.login:
            return '请登录后重试'
        profile_id = session.profile_id
        postdata = web.input()
        new_profile_username = postdata.get('profile_username').encode('utf-8')
        new_profile_welcome = postdata.get('profile_welcome').encode('utf-8')
        new_password = postdata.get('local_auth_password')
        
        bind_cnt = model.Profile(profile_id).profile_bind_cnt
        
        if new_password == "":
            #do not modify pswd
            profile_c = model.ProfileClass()
            profile_c.modProfile(profile_id, bind_cnt, new_profile_username, new_profile_welcome)
        else:
            profile_c = model.ProfileClass()
            profile_c.modProfile(profile_id, bind_cnt, new_profile_username, new_profile_welcome)

            local_auth_c = model.LocalAuthClass()
            local_auth = local_auth_c.getLocalAuthByProfileId(profile_id)
            local_auth_c.modLocalAuth(local_auth.local_auth_id, profile_id, new_password)
        return 'modify ok!'


class callback(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    def getTokenAndExpires(self):
        #发出请求, 从OAuth服务器端获得token和expires
        pass
    def getReqURL(self, base_url, **kwargs):
        #只能用来拼GET串......
        if base_url is None:
            raise Exception('missing required key base_url')
        #for items in kwargs.items():
        url_str = base_url + '?'
        for k, v in kwargs.iteritems():
            url_str = url_str + ("%s=%s" % (k, v)) + '&'
        return url_str[0:-1]
    def makePostReq(self, base_url, **kwargs):
        req = urllib2.Request(base_url, data=urllib.urlencode(kwargs))
        try:
            page = urllib2.urlopen(req)
            return eval(page.read(-1))
        except urllib2.HTTPError, e:
            print "Error Code:", e.code
            #return "Error Code:%s" % e.code
        except urllib2.URLError, e:
            print "Error Reason", e.reason
            #return "Error Reason:%s" % e.reason
        return None

class db_auth:
    def GET(self):
        session = web.config._session
        if session.login:
            profile_id = session.profile_id
        else:
            profile_id = 0
        douban_oauth = DoubanOauth(profile_id)
        douban_oauth.redirectToAuth()
        raise web.seeother('/')
    POST = GET

class db_callback(callback):
    def __init__(self):
        super(db_callback, self).__init__()
    def GET(self):
        douban_oauth = DoubanOauth()
        profile_id, token, expires, server_user_id = douban_oauth.authCallback()
        session = web.config._session
        session.oauth_access_token      = token
        session.oauth_server_user_id    = server_user_id
        session.oauth_expires           = expires
        session.from_where              = 'douban'
        raise web.seeother('/otherpassportbind?profile_id=%d' % profile_id)

class wb_auth:
    def GET(self):
        url = ''
        t1 = (SOCIALOAUTH_SITES[0], )
        socialsites = SocialSites(t1)
        for s in socialsites.list_sites_class():
            site = socialsites.get_site_object_by_class(s)
            url = site.authorize_url
        raise web.seeother(url)
        return url
    POST = GET

class wb_callback:
    def GET(self):
        sitename = 'wb_callback'
        code = web.input().get('code')
        logger = web.ctx.environ['wsgilog.logger']
        if code is None:
            logger.warning("wb guale guale guale, no code")
        socialsites = SocialSites(SOCIALOAUTH_SITES)
        s = socialsites.get_site_object_by_name(sitename)
        try:
            s.get_access_token(code)
        except SocialAPIError as e:
            logger = web.ctx.environ['wsgilog.logger']
            logger.warning("wb guale guale guale, get_token_error")

        logger.warning('haha success uid:%s' % s.uid)
        logger.warning('dir(s):%s' % dir(s))
        session = web.config._session
        session.from_where = 'weibo'
        oauth_server_user_id = ('weibo-%s' % s.uid)

        oauth_c = model.OauthClass()
        oauth_id, oauth_profile_id = oauth_c.getBindUserId(oauth_server_user_id)
        profile_id = session.profile_id

        if (not oauth_id is None) and (not oauth_profile_id is None):
            if profile_id == 0:
                session.profile_id  = oauth_profile_id
                session.login       = True
                raise web.seeother('/welcome')

        session.oauth_access_token      = s.access_token
        session.oauth_server_user_id    = oauth_server_user_id
        session.oauth_expires           = s.expires_in
        raise web.seeother('otherpassportbind?profile_id=%d' % session.profile_id)

        
class otherpassportbind:
    def check_session(self):
        session = web.config._session
        return session
    def incBindCnt(self, profile_id):
        try:
            profile = model.Profile(profile_id)
            profile_c = model.ProfileClass()
            profile_c.modProfile(profile.profile_id, profile.profile_bind_cnt + 1,
                                 profile.profile_username, profile.profile_welcome)
        except Exception, e:
            logger = web.ctx.environ['wsgilog.logger']
            logger.warning("profile_id:%d is not exist!" % profile_id)
            return False
        return True
    def GET(self):
        session = self.check_session()
        data = web.input()
        profile_id = int(data.get('profile_id'))
        if profile_id == 0:
            #如果不存在本地账号
            tt = Template(filename = './template/otherpassportbind.html')
            return tt.render(from_where = session.from_where)
        else:
            #如果已经存在本地账号, 则将本地账号的绑定值增加
            if self.incBindCnt(profile_id):
                return '绑定第三方账号成功'
            else:
                return '绑定第三方账号失败, 请重试'

    def POST(self):
        #新增profile表跟local_auth表建立本地账号
        #新增auth表
        session = self.check_session()
        postdata = web.input()
        logger = web.ctx.environ['wsgilog.logger']
        #logger.warning('i see you')       

        profile_username = postdata.get('profile_username').encode('utf-8')
        profile_welcome = postdata.get('profile_welcome').encode('utf-8')
        local_auth_password = postdata.get('local_auth_password')
        from_where = postdata.get('from_where')

        profile_c = model.ProfileClass()
        profile_id = profile_c.addProfile(1, profile_username, profile_welcome)

        local_auth_c = model.LocalAuthClass()
        local_auth_c.addLocalAuth(profile_id, local_auth_password)

        oauth_c = model.OauthClass()
        oauth_c.addOauth(profile_id, from_where, session.oauth_access_token,
                         session.oauth_server_user_id, session.oauth_expires)

        return '绑定成功, 您的用户名: %s 用户ID: %d, 请保存好用户ID, 凭ID登陆' % (profile_username, profile_id)

class exit:
    def GET(self):
        session = web.config._session
        session.kill()
        raise web.seeother('/')
        return '已经退出'
    POST = GET

class authorize:
    def GET(self):
        #显示所有的第三方账号的绑定情况
        session = web.config._session
        if not session.login:
            return '请登录后重试'
        profile_id = session.profile_id

        auth_link       = ['https://www.douban.com/service/auth2/auth?client_id=06774723affa83641365d56b0fef8a2c&redirect_uri=http://nwmlwb.iask.in/db_callback&response_type=code&scope=douban_basic_common',
                           'qqzone',
                           'weibo']
        #解除某个第三方应用的绑定, 若最后一个第三方账号已经被解除, 则该账号视为被注销, 无法登录
        auth_list_all   = ['douban', 'qqzone', 'weibo']
        auth_already    = []

        oauth_c = model.OauthClass()
        auth_list = oauth_c.getAuthInfoByProfileId(profile_id)
        no_auth_list = []

        for auth in auth_list:
            auth_already.append(auth['oauth_from'])
        for i in xrange(len(auth_list_all)):
            if auth_list_all[i] not in auth_already:
                no_auth_info = {}
                no_auth_info['auth_url'] = auth_link[i]
                no_auth_info['auth_name'] = auth_list_all[i]
                no_auth_list.append(no_auth_info)

        tt = Template(filename = './template/authorize_show.html')
        return tt.render(auth_list = auth_list, no_auth_list = no_auth_list,
                         auth_list_all = auth_list_all, auth_already = auth_already,
                         profile_id = session.profile_id, profile_welcome = session.welcome,
                         profile_username = session.username)
    def POST(self):
        #解除某个第三方应用的绑定, 若最后一个第三方账号已经被解除, 则该账号视为被注销, 无法登录
        session = web.config._session
        if not session.login:
            return '请登录后重试'
        profile_id = session.profile_id
        postdata = web.input()
        logger = web.ctx.environ['wsgilog.logger']
        logger.warning("authorize auth_from:%s" % postdata.get('auth_from'))


class authorize_mod:
    def GET(self):
        pass
