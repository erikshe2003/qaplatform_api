# -*- coding: utf-8 -*-

import flask
import route

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_taskassign
from model.mysql import model_mysql_taskinfo
from model.mysql import model_mysql_workerinfo

"""
    获取个人测试计划下接口测试任务的基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            返回测试任务基础配置数据及执行应用分配清单
"""


@route.check_token
@route.check_user
@route.check_auth
@route.check_get_parameter(
    ['taskId', int, 1, None]
)
def task_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "操作成功",
        "data": {
            "configuration": {},
            "assignList": []
        }
    }

    taskid = int(flask.request.args['taskId'])

    # 获取测试任务基础配置数据
    try:
        task_configuration_info = model_mysql_taskinfo.query.filter(
            model_mysql_taskinfo.taskId == taskid
        ).first()
    except Exception as e:
        api_logger.error("查询测试计划配置信息失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        try:
            task_assign_info = mysqlpool.session.query(
                model_mysql_taskassign.taskId,
                model_mysql_taskassign.assignId,
                model_mysql_taskassign.startTime,
                model_mysql_taskassign.finishTime,
                model_mysql_taskassign.status,
                model_mysql_taskassign.workerId,
                model_mysql_workerinfo.ip,
                model_mysql_workerinfo.port
            ).outerjoin(
                model_mysql_workerinfo,
                model_mysql_taskassign.workerId == model_mysql_workerinfo.workerId
            ).filter(
                model_mysql_taskassign.taskId == taskid,
            ).all()
        except Exception as e:
            api_logger.error("查询测试计划配置信息失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']

    # 格式化返回值
    response_json['data']['configuration']['taskId'] = taskid
    response_json['data']['configuration']['startTime'] = str(task_configuration_info.startTime) if task_configuration_info.startTime else None
    response_json['data']['configuration']['endTime'] = str(task_configuration_info.endTime) if task_configuration_info.endTime else None
    response_json['data']['configuration']['taskType'] = task_configuration_info.taskType
    response_json['data']['configuration']['planId'] = task_configuration_info.planId
    response_json['data']['configuration']['taskDescription'] = task_configuration_info.taskDescription
    response_json['data']['configuration']['startType'] = task_configuration_info.startType
    response_json['data']['configuration']['endType'] = task_configuration_info.endType
    response_json['data']['configuration']['errorType'] = task_configuration_info.errorType
    response_json['data']['configuration']['excuteTimes'] = task_configuration_info.excuteTimes
    response_json['data']['configuration']['vUser'] = task_configuration_info.vUser
    response_json['data']['configuration']['rampUpPeriod'] = task_configuration_info.rampUpPeriod
    for tai in task_assign_info:
        response_json['data']['assignList'].append({
            'taskId': tai.taskId,
            'assignId': tai.assignId,
            'startTime': str(tai.startTime) if tai.startTime else None,
            'finishTime': str(tai.finishTime) if tai.finishTime else None,
            'workerId': tai.workerId,
            'ip': tai.ip,
            'port': tai.port,
            'status': tai.status
        })

    return response_json
