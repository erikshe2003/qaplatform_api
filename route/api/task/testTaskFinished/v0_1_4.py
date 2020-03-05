# -*- coding: utf-8 -*-

import flask
import json
import route
import datetime

from sqlalchemy import and_

from handler.log import api_logger
from handler.pool import mysqlpool

from route.api.task import api_task

from model.mysql import model_mysql_workerinfo
from model.mysql import model_mysql_taskassign

"""
    测试任务运行结束
    ----校验
            校验worker是否存在
            校验task是否分配给了该worker
    ----操作
            写入结束时间
"""


@api_task.route('/testTaskFinished.json', methods=['post'])
@route.check_post_parameter(
    ['taskId', int, 1, None],
    ['uuid', str, 1, 100],
    ['finishTime', str, 19, 19]
)
def test_task_finished():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {}
    }

    # 取出taskId/uuid/finishTime
    task_id = flask.request.json['taskId']
    worker_uuid = flask.request.json['uuid']
    finish_time = flask.request.json['finishTime']

    # 校验finishTime是否合法
    try:
        datetime.datetime.strptime(finish_time, '%Y-%m-%d %H:%M:%S')
    except:
        return route.error_msgs['msg_value_type_error']

    # 根据uuid在查找workerId
    try:
        worker_data = model_mysql_workerinfo.query.filter(
            model_mysql_workerinfo.uniqueId == worker_uuid
        ).first()
    except Exception as e:
        api_logger.debug("worker_data query failed:" + repr(e))
        return route.error_msgs['msg_db_error']
    else:
        if worker_data is None:
            return route.error_msgs['msg_worker_not_exist']

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
        return route.error_msgs['msg_db_error']
    else:
        if assign_data is None:
            return route.error_msgs['msg_no_assign']
        else:
            assign_data.finishTime = finish_time
            mysqlpool.session.commit()

    return json.dumps(response_json)
