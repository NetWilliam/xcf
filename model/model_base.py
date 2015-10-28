import os
import sys
sys.path.append('/home/pi/source/xcf')

from conf import *
import pymysql.cursors
import pprint

class ModelBase(object):
    def __init__(self):
        self.db_con = pymysql.connect(host = DB_HOST, user = DB_USER, password = DB_PSWD,
                                      db = DB_DATABASE)
        self.cursor = self.db_con.cursor()
        #self.cursor.execute('SET NAMES utf8;')
    def __del__(self):
        self.cursor.close()
        self.db_con.close()

