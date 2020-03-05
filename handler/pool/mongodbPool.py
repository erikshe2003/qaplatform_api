# -*- coding: utf-8 -*-

from pymongo import MongoClient
from handler.config.database import databaseconfig
from handler.log import sys_logger


logmsg = "系统初始化|准备初始化mongodb连接池"
sys_logger.info(logmsg)
try:
    mongodb_client = MongoClient(
        host=databaseconfig.get("mongodb", "host"),
        port=int(databaseconfig.get("mongodb", "port")),
        maxPoolSize=100
    )
    mongodb_tasklog_pool = mongodb_client['tasklog']
    mongodb_tasklog_pool.authenticate(
        databaseconfig.get("mongodb", "username"),
        databaseconfig.get("mongodb", "password")
    )
except Exception as e:
    logmsg = "系统初始化|mongodb连接池初始化失败，失败原因：" + repr(e)
    sys_logger.error(logmsg)
    raise RuntimeError(logmsg)
logmsg = "系统初始化|mongodb连接池初始化结束"
sys_logger.info(logmsg)
