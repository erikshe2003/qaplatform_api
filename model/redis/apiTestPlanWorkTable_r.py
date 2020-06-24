# -*- coding: utf-8 -*-

import datetime

from handler.pool.redisPool import redispool
from handler.log import db_logger


class ApiTestPlanWorkTableR:
    def __init__(self):
        self.key = "apiTestPlanWorkTable"

    # 支持根据planId查询工作台缓存的内容
    def query_table(self, plan_id):
        try:
            data = redispool.hget("%s:%s" % (self.key, plan_id), "table")
            db_logger.debug("内容查询成功")
            return data
        except Exception as e:
            db_logger.error("内容查询失败，失败原因：" + repr(e))
            return None

    # 支持根据planId查询工作台缓存的时间
    def query_time(self, plan_id):
        try:
            data = redispool.hget("%s:%s" % (self.key, plan_id), "time")
            db_logger.debug("内容查询成功")
            return data
        except Exception as e:
            db_logger.error("内容查询失败，失败原因：" + repr(e))
            return None

    # 支持根据planId以及传入的内容存储
    def set_table(self, plan_id, value):
        try:
            redispool.hset("%s:%s" % (self.key, plan_id), "table", value)
            db_logger.debug("内容设定成功")
            return True
        except Exception as e:
            db_logger.error("内容设定失败，失败原因：" + repr(e))
            return False

    # 支持根据planId以及传入的内容存储
    def set_time(self, plan_id):
        try:
            redispool.hset("%s:%s" % (
                self.key, plan_id), "time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            db_logger.debug("内容设定成功")
            return True
        except Exception as e:
            db_logger.error("内容设定失败，失败原因：" + repr(e))
            return False

    # 根据plan_id删除缓存的工作台内容
    def delete(self, plan_id):
        try:
            redispool.hdel("%s:%s" % (self.key, plan_id), "table")
            redispool.hdel("%s:%s" % (self.key, plan_id), "time")
            logmsg = "内容数据删除成功"
            db_logger.debug(logmsg)
            return True
        except Exception as e:
            logmsg = "内容数据删除失败，失败原因：" + repr(e)
            db_logger.error(logmsg)
            return False