# -*- coding: utf-8 -*-

import flask
import route
import datetime

from sqlalchemy import and_

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_workerinfo
from model.mysql import model_mysql_taskassign

"""
    测试任务运行结果
    ----校验
            校验worker是否存在
            校验task是否分配给了该worker
    ----操作
            写入结束时间
"""


@route.check_post_parameter(
    ['taskId', int, 1, None],
    ['uuid', str, 1, 100],
    ['status', int, None, None]
)
def task_result_post():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "操作成功",
        "data": {}
    }

    # 取出taskId/uuid/finishTime
    task_id = flask.request.json['taskId']
    worker_uuid = flask.request.json['uuid']
    task_status = flask.request.json['status']

    # 根据uuid在查找workerId
    try:
        worker_data = model_mysql_workerinfo.query.filter(
            model_mysql_workerinfo.uniqueId == worker_uuid
        ).first()
    except Exception as e:
        api_logger.debug("worker_data query failed:" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if worker_data is None:
            return route.error_msgs[201]['msg_worker_not_exist']

    # 根据taskId以及workerId查询分配记录
    try:
        assign_data = model_mysql_taskassign.query.filter(
            and_(
                model_mysql_taskassign.taskId == task_id,
                model_mysql_taskassign.workerId == worker_data.workerId
            )
        ).first()
    except Exception as e:
        api_logger.debug("assign_data query failed:" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if assign_data is None:
            return route.error_msgs[201]['msg_no_assign']
        else:
            assign_data.status = task_status
            assign_data.updateTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if task_status == 10:
                assign_data.finishTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elif task_status == 3:
                assign_data.startTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            mysqlpool.session.commit()

    return response_json
