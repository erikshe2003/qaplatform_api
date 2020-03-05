# -*- coding: utf-8 -*-

from handler.pool.redisPool import redispool
from handler.log import db_logger


class RolePermissionR:
    def __init__(self):
        self.key = "rolePermission"

    # 支持根据角色id查询角色权限信息
    def query(self, role_id):
        try:
            data = redispool.hget(self.key, role_id)
            logmsg = "Redis查询|" + self.key + "查询成功"
            db_logger.debug(logmsg)
            return data
        except Exception as e:
            logmsg = "Redis查询|" + self.key + "查询失败，失败原因：" + repr(e)
            db_logger.error(logmsg)

    # 支持根据角色id增添角色权限信息
    def set(self, role_id, value):
        try:
            redispool.hset(self.key, role_id, value)
            logmsg = "Redis值设定|" + self.key + "值设定成功"
            db_logger.debug(logmsg)
            return True
        except Exception as e:
            logmsg = "Redis值设定|" + self.key + "值设定失败，失败原因：" + repr(e)
            db_logger.error(logmsg)
            return False

    # 支持根据角色id删除数据
    def delete(self, role_id):
        try:
            redispool.hdel(self.key, role_id)
            logmsg = "Redis值删除|" + self.key + "值删除成功"
            db_logger.debug(logmsg)
            return True
        except Exception as e:
            logmsg = "Redis值删除|" + self.key + "值删除失败，失败原因：" + repr(e)
            db_logger.error(logmsg)
            return False
