# -*- coding: utf-8 -*-

from handler.pool.redisPool import redispool_1
from handler.log.loggers import db_logger


class TaskLogR:
    def __init__(self):
        self.key = "taskLog:"

    # 支持根据任务id查询任务执行日志
    def query(self, taskid):
        try:
            new_key = self.key + str(taskid)
            data = redispool_1.smembers(new_key)
            logmsg = "Redis查询|db1|" + new_key + "查询成功"
            db_logger.debug(logmsg)
            return data
        except Exception as e:
            logmsg = "Redis查询|db1|" + new_key + "查询失败，失败原因：" + repr(e)
            db_logger.error(logmsg)

    def sadd(self, taskid, value):
        try:
            new_key = self.key + str(taskid)
            redispool_1.sadd(new_key, value)
            logmsg = "Redis值设定|db1|" + new_key + "值设定成功"
            db_logger.debug(logmsg)
            return True
        except Exception as e:
            logmsg = "Redis值设定|db1|" + new_key + "值设定失败，失败原因：" + repr(e)
            db_logger.error(logmsg)
            return False
