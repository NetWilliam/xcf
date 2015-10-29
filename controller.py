#!/usr/bin/env python
#! -*- coding:utf-8 -*-
import urllib, urllib2
from logging import warning as w_log
import web
import pprint
from mako.template import Template
from conf import *
import model
from conf.oauth_setting import *
from socialoauth import SocialSites, SocialAPIError

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

class db_auth:
    def GET(self):
        socialsites = SocialSites(SOCIALOAUTH_SITES)
        ss = socialsites.list_sites_class()
        site = socialsites.get_site_object_by_class(ss[2])
        url = site.authorize_url
        raise web.seeother(url)
    POST = GET

class db_callback():
    def GET(self):
        sitename = 'db_callback'
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

        session = web.config._session
        session.from_where = 'douban'
        oauth_server_user_id = ('douban-%s' % s.uid)

        oauth_c = model.OauthClass()
        oauth_id, oauth_profile_id = oauth_c.getBindUserId(oauth_server_user_id)
        profile_id = session.profile_id

        if (not oauth_id is None) and (not oauth_profile_id is None):
            if profile_id == 0 or profile_id == oauth_profile_id:
                # 三方账户已经绑定, 并且当前用户尚未登录
                # 已经绑定本地账户的用户通过三方账户登录
                session.profile_id  = oauth_profile_id
                session.login       = True
                raise web.seeother('/welcome')
            else:
                # 三方账户已经绑定, 试图再绑定, 抛出错误
                #raise web.seeother('/rebind_error')
                return '该三方账户已经绑定, 无法重复绑定'

        session.oauth_access_token      = s.access_token
        session.oauth_server_user_id    = oauth_server_user_id
        session.oauth_expires           = s.expires_in
        raise web.seeother('otherpassportbind?profile_id=%d' % session.profile_id)

class wb_auth:
    def GET(self):
        socialsites = SocialSites(SOCIALOAUTH_SITES)
        ss = socialsites.list_sites_class()
        site = socialsites.get_site_object_by_class(ss[0])
        url = site.authorize_url
        raise web.seeother(url)
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

        session = web.config._session
        session.from_where = 'weibo'
        oauth_server_user_id = ('weibo-%s' % s.uid)

        oauth_c = model.OauthClass()
        oauth_id, oauth_profile_id = oauth_c.getBindUserId(oauth_server_user_id)
        profile_id = session.profile_id

        if (not oauth_id is None) and (not oauth_profile_id is None):
            if profile_id == 0 or profile_id == oauth_profile_id:
                # 三方账户已经绑定, 并且当前用户尚未登录
                # 已经绑定本地账户的用户通过三方账户登录
                session.profile_id  = oauth_profile_id
                session.login       = True
                raise web.seeother('/welcome')
            else:
                # 三方账户已经绑定, 试图再绑定, 抛出错误
                #raise web.seeother('/rebind_error')
                return '该三方账户已经绑定, 无法重复绑定'

        session.oauth_access_token      = s.access_token
        session.oauth_server_user_id    = oauth_server_user_id
        session.oauth_expires           = s.expires_in
        raise web.seeother('otherpassportbind?profile_id=%d' % session.profile_id)

class qq_auth:
    def GET(self):
        socialsites = SocialSites(SOCIALOAUTH_SITES)
        ss = socialsites.list_sites_class()
        site = socialsites.get_site_object_by_class(ss[1])
        url = site.authorize_url
        raise web.seeother(url)
    POST = GET

class qq_callback:
    def GET(self):
        sitename = 'qq_callback'
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

        session = web.config._session
        session.from_where = 'qqzone'
        oauth_server_user_id = ('qqzone-%s' % s.uid)

        oauth_c = model.OauthClass()
        oauth_id, oauth_profile_id = oauth_c.getBindUserId(oauth_server_user_id)
        profile_id = session.profile_id

        if (not oauth_id is None) and (not oauth_profile_id is None):
            if profile_id == 0 or profile_id == oauth_profile_id:
                # 三方账户已经绑定, 并且当前用户尚未登录
                # 已经绑定本地账户的用户通过三方账户登录
                session.profile_id  = oauth_profile_id
                session.login       = True
                raise web.seeother('/welcome')
            else:
                # 三方账户已经绑定, 试图再绑定, 抛出错误
                #raise web.seeother('/rebind_error')
                return '该三方账户已经绑定, 无法重复绑定'

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
            oauth_c     = model.OauthClass()
            oauth_id    = oauth_c.addOauth(profile_id, session.from_where, session.oauth_access_token,
                                           session.oauth_server_user_id, session.oauth_expires)
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

        auth_link       = ['db_auth', 'qq_auth', 'wb_auth']
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
        auth_from_list = ['douban', 'qqzone', 'weibo']
        # 这个地方会不会出现两个豆瓣账号绑定同一个本地账号的问题呢?... 有空需要思考一下
        # 假设一个本地账号肯定只有一个三方账号
        auth_from   = postdata.get('auth_from')
        profile_id  = session.profile_id
        oauth_c     = model.OauthClass()
        oauth       = oauth_c.getOauthByProfileIdAndAuthFrom(profile_id, auth_from)
        #logger.warning('sql:%s' % oauth)
        oauth_c.delOauth(oauth.oauth_id)

        profile_c   = model.ProfileClass()
        profile     = model.Profile(profile_id)
        profile_c.modProfile(profile.profile_id, profile.profile_bind_cnt-1,
                             profile.profile_username, profile.profile_welcome)

        #logger.warning("authorize auth_from:%s" % postdata.get('auth_from'))
        raise web.seeother('/exit')


class authorize_mod:
    def GET(self):
        pass
