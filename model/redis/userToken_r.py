# -*- coding: utf-8 -*-

from handler.pool.redisPool import redispool
from handler.log import db_logger


class UserTokenR:
    def __init__(self):
        self.key = "userToken"

    # 支持根据邮箱地址查询token值以及token有效期
    def query(self, user_email):
        try:
            data = redispool.hget(self.key, user_email)
            logmsg = "Redis查询|" + self.key + "查询成功"
            db_logger.debug(logmsg)
            return data
        except Exception as e:
            logmsg = "Redis查询|" + self.key + "查询失败，失败原因：" + repr(e)
            db_logger.error(logmsg)

    # 支持根据邮箱地址缓存内容
    def set(self, user_email, value):
        try:
            redispool.hset(self.key, user_email, value)
            logmsg = "Redis值设定|" + self.key + "值设定成功"
            db_logger.debug(logmsg)
            return True
        except Exception as e:
            logmsg = "Redis值设定|" + self.key + "值设定失败，失败原因：" + repr(e)
            db_logger.error(logmsg)
            return False

    # 根据邮箱地址删除缓存token
    def delete(self, user_email):
        try:
            redispool.hdel(self.key, user_email)
            logmsg = "Redis值删除|" + self.key + "值对应缓存数据删除"
            db_logger.debug(logmsg)
            return True
        except Exception as e:
            logmsg = "Redis值删除|" + self.key + "值对应缓存数据删除，失败原因：" + repr(e)
            db_logger.error(logmsg)
            return False
