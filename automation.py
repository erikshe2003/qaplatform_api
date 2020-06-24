# -*- coding: utf-8 -*-

# 极课自动化测试平台实例

from gevent import monkey

monkey.patch_all()

from flask import Flask
from handler.log import sys_logger
from flask_sockets import Sockets

logmsg = "系统初始化|准备生成flask实例"
sys_logger.info(logmsg)
try:
    automation = Flask(__name__)
    automation.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
    sockets = Sockets(automation)
    logmsg = "系统初始化|flask实例生成成功"
    sys_logger.info(logmsg)
except Exception as e:
    logmsg = "系统初始化|flask实例生成失败，失败原因：" + repr(e)
    sys_logger.info(logmsg)
    raise RuntimeError(logmsg)

# 加载模块
from route.api.management import api_management
automation.register_blueprint(api_management, url_prefix="/api/management")
from route.api.plan import api_plan
automation.register_blueprint(api_plan, url_prefix="/api/plan")
from route.api.task import api_task
automation.register_blueprint(api_task, url_prefix="/api/task")
from route.api.test import api_test
automation.register_blueprint(api_test, url_prefix="/api/test")
from route.api.user import api_user
automation.register_blueprint(api_user, url_prefix="/api/user")

from route.socket.test import ws_test
sockets.register_blueprint(ws_test, url_prefix="/ws/test")
from route.socket.report import ws_report
sockets.register_blueprint(ws_report, url_prefix='/ws/report')
from route.socket.plan import ws_plan
sockets.register_blueprint(ws_plan, url_prefix='/ws/plan')
