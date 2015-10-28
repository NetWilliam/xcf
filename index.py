#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import web
from controller import *

import sys, logging
from wsgilog import WsgiLog#, LogIO

class Log(WsgiLog):
    def __init__(self, application):
        WsgiLog.__init__(
            self,
            application,
            logformat = '[%(asctime)s] %(filename)s:%(lineno)d(%(funcName)s): [%(levelname)s] %(message)s',
            tofile = True,
            file = '/home/pi/source/xcf/log/webpy.log',
            interval = 's',
            backups = 1)
        #sys.stdout = LogIO(self.logger, logging.INFO)
        #sys.stderr = LogIO(self.logger, logging.ERROR)

home = ''
os.environ['SCRIPT_NAME'] = home
os.environ['REAL_SCRIPT_NAME'] = home

urls = (
    '/(.*\.css)', 'cssStatics',
    '/(.*\.js)', 'jsStatics',
    '/', 'index',
    '/login', 'login',
    '/welcome', 'welcome',
    '/signup', 'signup',
    '/modify', 'modify',
    '/db_callback', 'db_callback',
    '/otherpassportbind', 'otherpassportbind',
    '/exit', 'exit',
    '/authorize_show', 'authorize_show',
    '/authorize_mod', 'authorize_mod',
)

app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore('sessions'),
            initializer = {'login': False, 'username': '', 'welcome': '', 'profile_id': 0,
                           'oauth_access_token': '', 'oauth_expires': '', 'oauth_server_user_id': '',
                           'from_where': '', 'bind_cnt': 0})

if __name__ == "__main__":
    #web.wsgi.runwsgi = lambda func, addr = None: web.wsgi.runfcgi(func, addr)
    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    web.debug = False
    web.config._session = session
    app.run(Log)
    #with open('/home/pi/source/xcf/log.txt') as f:
    #    f.write('xxx', 'r')
