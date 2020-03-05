# -*- coding: utf-8 -*-

from automation import automation
from flask_sqlalchemy import SQLAlchemy
from handler.config.database import databaseconfig
from handler.log import sys_logger


logmsg = "系统初始化|准备初始化mysql连接池"
sys_logger.info(logmsg)
try:
    automation.config['SQLALCHEMY_DATABASE_URI'] = databaseconfig.get("mysql", "uri")
    automation.config['SQLALCHEMY_POOL_SIZE'] = databaseconfig.getint("mysql", "poolsize")
    automation.config['SQLALCHEMY_MAX_OVERFLOW'] = databaseconfig.getint("mysql", "overflow")
    automation.config['SQLALCHEMY_POOL_TIMEOUT'] = databaseconfig.getint("mysql", "timeout")
    automation.config['SQLALCHEMY_POOL_RECYCLE'] = databaseconfig.getint("mysql", "recycle")
    automation.config['SQLALCHEMY_ECHO'] = False
    automation.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    mysqlpool = SQLAlchemy(automation)
    logmsg = "系统初始化|mysql连接池初始化成功"
    sys_logger.info(logmsg)
except Exception as e:
    logmsg = "系统初始化|mysql连接池初始化失败，失败原因：" + repr(e)
    sys_logger.error(logmsg)
    raise RuntimeError(logmsg)
logmsg = "系统初始化|mysql连接池初始化结束"
sys_logger.info(logmsg)
