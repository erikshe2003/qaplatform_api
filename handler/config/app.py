# -*- coding: utf-8 -*-

from configparser import ConfigParser
from handler.log import sys_logger


appconfig = ConfigParser()
logmsg = "系统初始化|准备读取环境配置文件生成配置对象"
sys_logger.info(logmsg)
try:
    appconfig.read(filenames="config/app.ini", encoding="utf-8")
    logmsg = "系统初始化|环境配置文件读取成功，成功生成配置对象"
    sys_logger.debug(logmsg)
except Exception as e:
    logmsg = "系统初始化|环境配置文件读取失败，失败原因：" + repr(e)
    sys_logger.error(logmsg)
    raise RuntimeError(logmsg)
logmsg = "系统初始化|环境配置对象生成结束"
sys_logger.info(logmsg)
