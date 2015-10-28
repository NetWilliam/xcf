#!/usr/bin/env python
#! -*- coding:utf-8 -*-
import urllib, urllib2
from logging import warning as w_log
import web
import pprint
from mako.template import Template
from conf import *
import model

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
        if new_password == "":
            #do not modify pswd
            profile_c = model.ProfileClass()
            profile_c.modProfile(profile_id, new_profile_username, new_profile_welcome)
        else:
            profile_c = model.ProfileClass()
            profile_c.modProfile(profile_id, new_profile_username, new_profile_welcome)

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


class db_callback(callback):
    def __init__(self):
        super(db_callback, self).__init__()
    def getTokenAndExpires(self, **kwargs):
        code = kwargs['code']
        post_url = DB_OAUTH_URL + '/token'
        print 'douban post_url:', post_url
        ret = self.makePostReq(post_url, code = code, client_id = DB_APP_KEY,
                               client_secret = DB_APP_SECRET, redirect_uri = DB_CALLBACK,
                               grant_type = 'authorization_code')
        if ret is None:
            #请求失败处理
            raise web.seeother('fault.html')

        oauth_access_token      = ret['access_token']
        oauth_expires           = ret['expires_in']
        server_user_id          = ret['douban_user_id']

        #这里数据库中的oauth_ser_user_id字段需要加上来自哪个平台的前缀, 以保证在整张表中的唯一性
        oauth_server_user_id    = ('douban-%s' % server_user_id)

        oauth_c = model.OauthClass()
        oauth_id, oauth_profile_id = oauth_c.getBindUserId(oauth_server_user_id)
        session = web.config._session
        if oauth_id is None and oauth_profile_id is None:
            #该用户的第三方账户尚未绑定本地账号, 转跳到绑定页面绑定之
            session.oauth_access_token      = oauth_access_token
            session.oauth_expires           = oauth_expires
            session.oauth_server_user_id    = oauth_server_user_id
            session.from_where              = 'douban'
            session.bind_cnt                = -1
            raise web.seeother('/otherpassportbind')
        else:
            #该用户的第三方账号已经绑定本地账号, 不允许重复绑定
            if session.login and session.profile_id != oauth_profile_id:
                #试图将一个三方账号重复绑定, 这种情况直接拒绝
                raise web.seeother('fault.html')
            else:
                #登录已经存在的账户, 刷新session, 重定向到主页君即可
                session.login = True
                session.profile_id = oauth_profile_id
                raise web.seeother('/welcome')

    def GET(self):
        getdata = web.input()
        code = getdata.get('code')
        
        return self.getTokenAndExpires(code = code)
        #return 'authorize return your code: %s' % code

class otherpassportbind:
    def check_session(self):
        session = web.config._session
        if session.bind_cnt == 0:
            raise web.seeother('fault.html')
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
        if not session.login:
            #如果不存在本地账号
            tt = Template(filename = './template/otherpassportbind.html')
            return tt.render(from_where = session.from_where)
        else:
            #如果已经存在本地账号, 则将本地账号的值增加
            if self.incBindCnt(session.profile_id):
                return '绑定第三方账号成功'
            else:
                return '绑定第三方账号失败, 请重试'

    def POST(self):
        #修改oauth表跟profile表
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
        return '已经退出'
    POST = GET

class authorize_show:
    def GET(self):
        session = web.config._session
        if not session.login:
            return '请登录后重试'
        auth_list = []
        profile_id = session.profile_id
        

        tt = Template(filename = './template/authorize_show.html')
        return tt.render()
        pass
    POST = GET

class authorize_mod:
    def GET(self):
        pass
