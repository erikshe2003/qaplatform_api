# -*- coding: utf-8 -*-

import flask
import json
import route
import datetime
import re

from handler.log import api_logger
from handler.pool import mysqlpool
from handler.config import databaseconfig

from model.mysql import model_mysql_workerinfo

"""
    接收来自测试任务执行应用的注册请求-api路由
    ----校验
            校验传参
    ----操作
            判断应用传递的数据
"""


@route.check_post_parameter(
    ['uuid', str, 1, 100],
    ['ip', str, 1, 100],
    ['port', int, 1025, 65534]
)
def worker_post():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "操作成功",
        "data": {
            "worker_id": None,
            "log_ip": None,
            "log_port": None,
            "log_password": None
        }
    }

    # 检查ip格式是否合法
    worker_ip = flask.request.json['ip']
    error_msg = {"code": 201, "msg": "ip地址非法", "data": {}}
    compile_ip = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if not compile_ip.match(worker_ip):
        return json.dumps(error_msg)

    # 至数据库中查询uuid是否存在
    worker_uuid = flask.request.json['uuid']
    try:
        mysql_worker = model_mysql_workerinfo.query.filter(
            model_mysql_workerinfo.uniqueId == worker_uuid
        ).first()
        api_logger.debug(worker_uuid + "的workerInfo信息读取成功")
    except Exception as e:
        api_logger.error(worker_uuid + "的workerInfo信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        # 如果未查询到记录，则新增记录
        if mysql_worker is None:
            mysql_worker = model_mysql_workerinfo(
                uniqueId=worker_uuid,
                ip=worker_ip,
                port=flask.request.json['port'],
                status=1,
                createTime=datetime.datetime.now(),
                updateTime=datetime.datetime.now()
            )
            mysqlpool.session.add(mysql_worker)
        # 如果查询到了记录，则更新记录
        else:
            mysql_worker.ip = worker_ip
            mysql_worker.port = flask.request.json['port']
            mysql_worker.status = 1
            mysql_worker.updateTime = datetime.datetime.now()
        try:
            mysqlpool.session.commit()
            api_logger.debug(worker_uuid + "的workerInfo信息新增/更新成功")
        except Exception as e:
            api_logger.debug(worker_uuid + "的workerInfo信息新增/更新失败，失败原因:" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            # 没问题的话返回redis相关信息给worker
            response_json['data']['worker_id'] = mysql_worker.workerId
            response_json['data']['log_ip'] = databaseconfig.get('mongodb', 'host')
            response_json['data']['log_port'] = databaseconfig.get('mongodb', 'port')
            response_json['data']['log_name'] = databaseconfig.get('mongodb', 'username')
            response_json['data']['log_password'] = databaseconfig.get('mongodb', 'password')
            return response_json
