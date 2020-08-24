# -*- coding: utf-8 -*-

from redis import Redis, ConnectionPool
from handler.config.database import databaseconfig
from handler.log import sys_logger

logmsg = "系统初始化|准备初始化redis连接池"
sys_logger.info(logmsg)
try:
    pool = ConnectionPool(
        host=databaseconfig.get("redis", "host"),
        port=int(databaseconfig.get("redis", "port")),
        password=databaseconfig.get("redis", "password") if databaseconfig.get("redis", "password") else None,
        max_connections=int(databaseconfig.get("redis", "max_connections")),
        health_check_interval=30
    )
    pool_1 = ConnectionPool(
        host=databaseconfig.get("redis", "host"),
        port=int(databaseconfig.get("redis", "port")),
        password=databaseconfig.get("redis", "password") if databaseconfig.get("redis", "password") else None,
        max_connections=int(databaseconfig.get("redis", "max_connections")),
        health_check_interval=30,
        db=1
    )
    redispool = Redis(connection_pool=pool)
    redispool_1 = Redis(connection_pool=pool_1)
    logmsg = "系统初始化|redis连接池初始化成功"
    sys_logger.info(logmsg)
except Exception as e:
    logmsg = "系统初始化|redis连接池初始化失败，失败原因：" + repr(e)
    sys_logger.error(logmsg)
    raise RuntimeError(logmsg)
logmsg = "系统初始化|redis连接池初始化结束"
sys_logger.info(logmsg)
