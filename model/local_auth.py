#! -*- coding:utf8 -*-
from model_base import ModelBase

class LocalAuthClass(ModelBase):
    def __init__(self):
        super(LocalAuthClass, self).__init__()
    def addLocalAuth(self, local_auth_profile_id, local_auth_password):
        sql_cmd = ('INSERT INTO local_auth (local_auth_profile_id, local_auth_password)'
                   ' VALUES (%d, "%s")' % (local_auth_profile_id, local_auth_password))
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID()')
        new_id = self.cursor.fetchall()[0][0]
        return new_id
    def delLocalAuth(self, local_auth_id):
        sql_cmd = ('DELETE FROM local_auth WHERE local_auth_id = %d' % local_auth_id)
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
    def modLocalAuth(self, local_auth_id, local_auth_profile_id, local_auth_password):
        sql_cmd = ('UPDATE local_auth SET local_auth_profile_id=%d, local_auth_password="%s"'
                   ' WHERE local_auth_id = %d' % (local_auth_profile_id, local_auth_password,
                   local_auth_id))
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
    def getLocalAuth(self, local_auth_id):
        return LocalAuth(local_auth_id)
    def getLocalAuthByProfileId(self, profile_id):
        sql_cmd = ('SELECT local_auth_id FROM local_auth WHERE local_auth_profile_id = %d' % profile_id)
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
        res = self.cursor.fetchall()
        if len(res) == 0:
            return False
        rarr = res[0]
        return self.getLocalAuth(rarr[0])
    def verifyLocalAuth(self, profile_id, local_auth_password):
        if not isinstance(profile_id, int):
            profile_id = int(profile_id)
        sql_cmd = ('SELECT local_auth_password FROM local_auth WHERE local_auth_profile_id=%d' % profile_id)
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
        res = self.cursor.fetchall()
        if len(res) == 0:
            return False;
        rarr = res[0]
        if local_auth_password == rarr[0]:
            #还要看该账号是否所有关联的三方账号都被取消绑定了, 如果是, 则认为该账号注销, 不能登录
            import profile
            profile_obj = profile.Profile(profile_id)
            if profile_obj.profile_bind_cnt <= 0:
                return False
            else:
                return True
        return False

class LocalAuth(ModelBase):
    def __init__(self, local_auth_id):
        super(LocalAuth, self).__init__()
        self.local_auth_id = local_auth_id
        sql_cmd = ('SELECT * FROM local_auth WHERE local_auth_id = %d' % local_auth_id)
        self.cursor.execute(sql_cmd)
        res = self.cursor.fetchall()
        if len(res) == 0:
            raise Exception('LocalAuth id:%d not exist!' % local_auth_id)
        rarr = res[0]
        self.local_auth_profile_id      = rarr[1]
        self.local_auth_password        = rarr[2]

if __name__ == "__main__":
    lac = LocalAuthClass()
    new_id = lac.addLocalAuth(1234, 'adminpswd')
    print 'new_id:', new_id
    la = lac.getLocalAuth(new_id)
    print 'local id:', la.local_auth_id, ' profile_id:', la.local_auth_profile_id, ' pswd:',la.local_auth_password
    lac.modLocalAuth(new_id, 4567, 'password')
    print 'mod done'
    la = lac.getLocalAuth(new_id)
    print 'local id:', la.local_auth_id, ' profile_id:', la.local_auth_profile_id, ' pswd:',la.local_auth_password
    lac.delLocalAuth(new_id)
    print 'del done'

    if lac.verifyLocalAuth(1001, 'adminpswd'):
        print 'profile_id:1234, pswd:"adminpswd" exist'
    else:
        print 'profile_id:1234, pswd:"adminpswd" not exist'
