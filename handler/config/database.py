# -*- coding: utf-8 -*-

from configparser import ConfigParser
from handler.log import sys_logger


databaseconfig = ConfigParser()
logmsg = "系统初始化|准备读取数据库配置文件生成配置对象"
sys_logger.info(logmsg)
try:
    databaseconfig.read(filenames="config/database.ini", encoding="utf-8")
    logmsg = "系统初始化|数据库配置文件读取成功，成功生成配置对象"
    sys_logger.debug(logmsg)
except Exception as e:
    logmsg = "系统初始化|数据库配置文件读取失败，失败原因：" + repr(e)
    sys_logger.error(logmsg)
    raise RuntimeError(logmsg)
logmsg = "系统初始化|数据库配置对象生成结束"
sys_logger.info(logmsg)
