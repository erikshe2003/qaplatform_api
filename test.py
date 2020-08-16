# -*- coding: utf-8 -*-

from automation import automation
from handler.log import sys_logger
from handler.config import appconfig
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler


if __name__ == '__main__':
    logmsg = "系统初始化|准备启动测试环境"
    sys_logger.info(logmsg)
    try:
        # 不能在生产环境中执行本文件
        # automation.run(debug=False, host=appconfig.get("api", "host"), port=int(appconfig.get("api", "port")))
        server = pywsgi.WSGIServer(
            (appconfig.get("api", "host"), int(appconfig.get("api", "port"))),
            automation,
            handler_class=WebSocketHandler
        )
        print('服务已启动')
        server.serve_forever()
    except Exception as e:
        logmsg = "系统初始化|测试环境启动失败，失败原因：" + repr(e)
        sys_logger.error(logmsg)
    logmsg = "系统初始化|测试环境启动结束"
    sys_logger.info(logmsg)

