# -*- coding: utf-8 -*-

"""
    获取个人测试计划下接口测试任务的列表-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            查询测试任务
            构建测试任务清单数据，并最终返回
"""

import flask
import json
import route

from sqlalchemy import and_

from handler.log import api_logger

from model.mysql import model_mysql_taskinfo


@route.check_token
@route.check_user
# @route.check_auth
@route.check_get_parameter(
    ['page', int, 1, None],
    ['planId', int, 1, None],
    ['num', int, 1, None]
)
def task_list_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "操作成功",
        "data": {
            "total": 0,
            "task_list": []
        }
    }

    page = int(flask.request.args['page'])
    num = int(flask.request.args['num'])
    planid = int(flask.request.args['planId'])

    # 获取测试任务数据
    try:
        tasks = model_mysql_taskinfo.query.filter(
            and_(
                model_mysql_taskinfo.planId == planid,
                model_mysql_taskinfo.taskType == 1
            )
        ).order_by(
            model_mysql_taskinfo.taskId.desc()
        ).limit(
            num
        ).offset(
            (page - 1) * num
        ).all()
    except Exception as e:
        api_logger.error("获取固定时间段内开始执行的历史任务数据失败，表：model_mysql_taskassign，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    # 格式化返回值
    response_json['data']['total'] = len(tasks)
    for task in tasks:
        response_json['data']['task_list'].append({
            'taskId': task.taskId,
            'description': task.taskDescription,
            'startTime': str(task.startTime)
        })

    return response_json
