#! -*- coding:utf-8 -*-
from model_base import ModelBase

class ProfileClass(ModelBase):
    def __init__(self):
        super(ProfileClass, self).__init__()
    def addProfile(self, profile_bind_cnt, profile_username, profile_welcome):
        sql_cmd = ('INSERT INTO profile (profile_bind_cnt, profile_username, profile_welcome) VALUES(%d, "%s", "%s")'
                   % (profile_bind_cnt, profile_username, profile_welcome))
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID()')
        new_id = self.cursor.fetchall()[0][0]
        return new_id
    def delProfile(self, profile_id):
        sql_cmd = ('DELETE FROM profile WHERE profile_id = %d' % profile_id)
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
    def modProfile(self, profile_id, profile_bind_cnt, profile_username, profile_welcome):
        sql_cmd = ('UPDATE profile SET profile_bind_cnt=%d, profile_username="%s", profile_welcome="%s"'
                   ' WHERE profile_id=%d' % (profile_bind_cnt, profile_username, profile_welcome, profile_id))
        print 'modProfile sql_cmd:', sql_cmd
        self.cursor.execute(sql_cmd)
        self.db_con.commit()
    def getProfile(self, profile_id):
        return Profile(profile_id)

class Profile(ModelBase):
    def __init__(self, profile_id):
        super(Profile, self).__init__()
        if not isinstance(profile_id, int):
            profile_id = int(profile_id)
        self.profile_id = profile_id
        sql_cmd = ('SELECT * FROM profile WHERE profile_id = %d' % profile_id)
        self.cursor.execute(sql_cmd)
        res = self.cursor.fetchall()
        if len(res) == 0:
            raise Exception('Profile id:%d not exist!' % profile_id)
        rarr = res[0]
        '''
        for item in rarr:
            try:
                item + ''
                print item.encode('utf-8')
            except Exception, e:
                print item
        '''
        self.profile_bind_cnt   = rarr[1]
        self.profile_username   = rarr[2]
        self.profile_welcome    = rarr[3]

if __name__ == "__main__":
    pc = ProfileClass()
    print 'new profile id:', pc.addProfile(1, 'liuzilong', '你好')
    pc.modProfile(1001, 2, '刘子龙', '人望和平, 当备战争')
    pc.delProfile(1000)
    pc.getProfile(1000)
