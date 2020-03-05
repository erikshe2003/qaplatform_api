# -*- coding: utf-8 -*-

import logging
from logging.config import fileConfig


try:
    # 加载配置文件
    fileConfig("config/log.ini")
    # 创建日志记录器,并加入文本日志处理器
    sys_logger = logging.getLogger("sys")
    api_logger = logging.getLogger("api")
    db_logger = logging.getLogger("db")
    logmsg = "系统初始化|日志配置文件读取成功，成功生成日志记录器"
    sys_logger.debug(logmsg)
except Exception as e:
    logmsg = "系统初始化|日志配置文件读取失败，失败原因：" + repr(e)
    raise RuntimeError(logmsg)
