#! -*- coding:utf-8 -*-
from model_base import ModelBase
import pprint

class OauthClass(ModelBase):
    def __init__(self):
        super(OauthClass, self).__init__()
    def addOauth(self, user_id, oauth_name, oauth_access_token, oauth_server_user_id, oauth_expires):
        sql_cmd = ('INSERT INTO oauth (oauth_profile_id, oauth_from, oauth_access_token, oauth_server_user_id, oauth_expires)'
                   ' VALUES (%d, "%s", "%s", "%s", %d)' % (user_id, oauth_name, oauth_access_token, oauth_server_user_id, oauth_expires))
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID()')
        new_id = self.cursor.fetchall()[0][0]
        return new_id

    def delOauth(self, oauth_id):
        sql_cmd = ('DELETE FROM oauth WHERE oauth_id = %d' % oauth_id)
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
    def modOauth(self, oauth_id, oauth_profile_id, oauth_from, oauth_access_token, oauth_server_user_id, oauth_expires):
        sql_cmd = ('UPDATE oauth SET oauth_profile_id=%d, oauth_from="%s", oauth_access_token="%s",'
                   ' oauth_server_user_id="%s", oauth_expires=%d WHERE oauth_id=%d' % (oauth_profile_id,
                   oauth_from, oauth_access_token, oauth_server_user_id, oauth_expires, oauth_id))
        print sql_cmd
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
    def getOauth(self, oauth_id):
        return Oath(oauth_id)
    def getBindUserId(self, server_user_id):
        sql_cmd = ('SELECT oauth_id, oauth_profile_id FROM oauth WHERE oauth_server_user_id="%s"'
                   % (server_user_id))
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
        res = self.cursor.fetchall()
        if len(res) == 0:
            return None, None
        rarr = res[0]
        return rarr
    def getAuthInfoByProfileId(self, profile_id):
        sql_cmd = ('SELECT * FROM oauth WHERE oauth_profile_id=%d ORDER BY oauth_from' % profile_id)
        self.cursor.execute(sql_cmd)
        self.db_con.commit()

        auth_info_list = []
        res = self.cursor.fetchall()
        for row in res:
            auth_info = {}
            auth_info['oauth_id']               = row[0]
            auth_info['oauth_profile_id']       = row[1]
            auth_info['oauth_from']             = row[2]
            auth_info['oauth_access_token']     = row[3]
            auth_info['oauth_server_user_id']   = row[4]
            auth_info['oauth_expires']          = row[5]
            auth_info_list.append(auth_info)
        return auth_info_list
    def getOauthByProfileIdAndAuthFrom(self, profile_id, auth_from):
        sql_cmd = ('SELECT oauth_id FROM oauth WHERE oauth_profile_id=%d AND oauth_from="%s"'
                    % (profile_id, auth_from))
        #return sql_cmd
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
        res = self.cursor.fetchall()
        if len(res) <= 0:
            return None
        rarr = res[0]
        return Oauth(rarr[0])


class Oauth(ModelBase):
    def __init__(self, oauth_id):
        super(Oauth, self).__init__()
        self.oauth_id = oauth_id
        sql_cmd = ('SELECT * FROM oauth WHERE oauth_id = %d' % oauth_id)
        self.cursor.execute(sql_cmd)
        res = self.cursor.fetchall()
        if len(res) == 0:
            raise Exception('Oauth id:%d not exist!' % oauth_id)
        rarr = res[0]
        self.oauth_profile_id       = rarr[1]
        self.oauth_from             = rarr[2]
        self.oauth_access_token     = rarr[3]
        self.oauth_server_user_id   = rarr[4]
        self.oauth_expires          = rarr[5]

if __name__ == "__main__":
    oa = OauthClass()
    #usr_id = oa.addOauth(1, 'ik', '你好', 'mlxid', 1000)
    #oa.modOauth(usr_id, 1, 'douban', '123abc', '1000', 3600)
    #print 'the new oa id is:', usr_id
    oae = Oauth(1000)
    #oac = Oauth(1008)
    #print oae.oauth_access_token.decode('utf-8')
    try:
        oad = Oauth(111111111)
    except Exception, e:
        print e

    oid, opid = oa.getBindUserId('1000')
    print oid, opid
    oid, opid = oa.getBindUserId('10000')
    print oid, opid
    
    oax = Oauth(1000)
    oa.modOauth(oax.oauth_id, oax.oauth_profile_id, '黄浦江', oax.oauth_access_token, oax.oauth_server_user_id, oax.oauth_expires)
    print oa.getAuthInfoByProfileId(1000)
    oa.modOauth(oax.oauth_id, oax.oauth_profile_id, 'douban', oax.oauth_access_token, oax.oauth_server_user_id, oax.oauth_expires)

