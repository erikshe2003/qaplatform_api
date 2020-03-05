# -*- coding: utf-8 -*-

from handler.config import mailconfig
from .public import PublicMailer
from handler.log import sys_logger


logmsg = "系统初始化|准备初始化公共邮件服务"
sys_logger.info(logmsg)
try:
    publicmailer = PublicMailer(
        address=mailconfig.get("public", "address"),
        password=mailconfig.get("public", "password"),
        smtp_host=mailconfig.get("smtp", "host"),
        smtp_port=int(mailconfig.get("smtp", "port")),
        smtp_ssl=bool(mailconfig.get("smtp", "ssl"))
    )
    logmsg = "系统初始化|公共邮件服务初始化成功"
    sys_logger.debug(logmsg)
except Exception as e:
    logmsg = "系统初始化|公共邮件服务初始化失败，失败原因：" + repr(e)
    sys_logger.error(logmsg)
    raise RuntimeError(logmsg)
logmsg = "系统初始化|公共邮件服务初始化结束"
sys_logger.info(logmsg)