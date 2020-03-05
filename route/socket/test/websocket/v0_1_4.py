# -*- coding: utf-8 -*-

import gevent
import time

from route.socket.test import ws_test


@ws_test.route('/echo')
def echo_socket(ws):
    while not ws.closed:
        # 监听来自前端的请求方式，判断执行什么代码
        action = ws.receive()
        if action and type(action) is str:
            if 'getReportData' in action:
                ws.send('succeed')
                # 监听来自前端的taskId
                task_id = ws.receive()
                # 查询mysql中对应数据
                ws.send('查询mysql成功啦')
                get_flag = True
                while get_flag:
                    # 查询redis中数据
                    ws.send('查询redis成功啦')
                    # 格式化日志数据
                    ws.send('格式化redis成功啦')
                    # 回传格式化日志数据
                    ws.send(str(time.time()))
                    # 监听来自前端的taskId
                    re_get = ws.receive()
                    if not re_get or 'get' not in re_get:
                        get_flag = False
                ws.close()
            else:
                ws.send('fail')
                ws.close()
        else:
            ws.send('fail')
            ws.close()
