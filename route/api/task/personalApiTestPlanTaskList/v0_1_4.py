# -*- coding: utf-8 -*-

import flask
import json
import route
import time

from sqlalchemy import and_, func, or_

from handler.log import api_logger
from handler.pool import mysqlpool

from route.api.task import api_task

from model.mysql import model_mysql_taskassign
from model.mysql import model_mysql_taskinfo
from model.mysql import model_mysql_planversion
from model.mysql import model_mysql_planinfo

"""
    获取已执行完成的历史任务列表-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            按照执行时间条件来查询已执行完成的测试任务（排除进行中的任务其他任务都归历史任务）
            构建测试任务清单数据，并最终返回
"""


@api_task.route('/historyTaskQuery.json', methods=['post'])
@route.check_token
@route.check_user
@route.check_auth
@route.check_post_parameter(
    ['page', int, 1, None],
    ['num', int, 1, None]
)
def history_task_query():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {
            "total": 0,
            "task_list": []
        }
    }

    page = flask.request.json['page']
    num = flask.request.json['num']

    # 当没有传开始时间,则默认开始时间为1970-01-01 00:00:00，传了开始时间则验证开始时间格式
    starttime = '1970-01-01 00:00:00'
    if 'startTime' in flask.request.json:
        starttime = flask.request.json['startTime']
        try:
            time.strptime(starttime, '%Y-%m-%d %H:%M:%S')
        except:
            return route.error_msgs['msg_data_error']

    # 当没有传结束时间,则默认结束时间为9999-01-01 00:00:00，传了结束时间则验证结束时间格式
    endtime = '9999-01-01 00:00:00'
    if 'endTime' in flask.request.json:
        endtime = flask.request.json['endTime']
        try:
            time.strptime(endtime, '%Y-%m-%d %H:%M:%S')
        except:
            return route.error_msgs['msg_data_error']

    # 当参数中传了planId，则判断planId是否为数字
    planid = None
    if 'planId' in flask.request.json:
        planid = flask.request.json['planId']
        if not isinstance(planid, int):
            return route.error_msgs['msg_data_error']

    if planid:
        # 获取固定时间段内开始执行的历史任务总条数（排除进行中的任务其他任务都归历史任务）
        try:
            tasks_count = mysqlpool.session.query(
                model_mysql_taskassign.taskId.label('taskId'),
                func.group_concat(model_mysql_taskassign.status).label('status'),
                func.max(model_mysql_taskassign.finishTime).label('real_endTime'),
                model_mysql_taskinfo.startTime.label('starTime'),
                model_mysql_taskinfo.endTime.label('endTime'),
                model_mysql_taskinfo.taskType.label('taskType'),
                model_mysql_taskinfo.versionId.label('v_id'),
                model_mysql_planversion.versionTitle.label('v_name'),
                model_mysql_taskinfo.planId.label('plan_id'),
                model_mysql_planinfo.planTitle.label('plan_name'),
                model_mysql_planinfo.planType.label('plan_type'),
                model_mysql_taskinfo.taskDescription.label('description'),
                model_mysql_taskinfo.startType.label('startType'),
                model_mysql_taskinfo.endType.label('endType'),
                model_mysql_taskinfo.excuteTimes.label('excuteTimes'),
                model_mysql_taskinfo.errorType.label('errorType'),
                model_mysql_taskinfo.vUser.label('vUser'),
                model_mysql_taskinfo.rampUpPeriod.label('rampUpPeriod')
            ).outerjoin(
                model_mysql_taskinfo,
                model_mysql_taskassign.taskId == model_mysql_taskinfo.taskId
            ).outerjoin(
                model_mysql_planversion,
                model_mysql_taskinfo.versionId == model_mysql_planversion.versionId
            ).outerjoin(
                model_mysql_planinfo,
                model_mysql_taskinfo.planId == model_mysql_planinfo.planId
            ).filter(
                and_(
                    model_mysql_taskinfo.startTime >= starttime,
                    model_mysql_taskinfo.startTime <= endtime,
                    model_mysql_taskinfo.planId == planid,
                    model_mysql_taskinfo.taskType > 2,
                    model_mysql_planversion.versionId.isnot(None)
                )
            ).group_by(
                model_mysql_taskassign.taskId
            ).having(
                func.count(model_mysql_taskassign.assignId) == func.sum(
                    func.if_(or_(
                        model_mysql_taskassign.status == -1,
                        model_mysql_taskassign.finishTime.isnot(None)
                    ), 1, 0)
                )
            ).all()

        except Exception as e:
            api_logger.error("获取固定时间段内开始执行的历史任务总条数失败，表：model_mysql_taskassign，失败原因：" + repr(e))
            return route.error_msgs['msg_db_error']

        # 获取固定时间段内开始执行的历史任务数据（排除进行中的任务其他任务都归历史任务）
        try:
            tasks = mysqlpool.session.query(
                model_mysql_taskassign.taskId.label('taskId'),
                func.group_concat(model_mysql_taskassign.status).label('status'),
                func.max(model_mysql_taskassign.finishTime).label('real_endTime'),
                model_mysql_taskinfo.startTime.label('starTime'),
                model_mysql_taskinfo.endTime.label('endTime'),
                model_mysql_taskinfo.taskType.label('taskType'),
                model_mysql_taskinfo.versionId.label('v_id'),
                model_mysql_planversion.versionTitle.label('v_name'),
                model_mysql_taskinfo.planId.label('plan_id'),
                model_mysql_planinfo.planTitle.label('plan_name'),
                model_mysql_planinfo.planType.label('plan_type'),
                model_mysql_taskinfo.taskDescription.label('description'),
                model_mysql_taskinfo.startType.label('startType'),
                model_mysql_taskinfo.endType.label('endType'),
                model_mysql_taskinfo.excuteTimes.label('excuteTimes'),
                model_mysql_taskinfo.errorType.label('errorType'),
                model_mysql_taskinfo.vUser.label('vUser'),
                model_mysql_taskinfo.rampUpPeriod.label('rampUpPeriod')
            ).outerjoin(
                model_mysql_taskinfo,
                model_mysql_taskassign.taskId == model_mysql_taskinfo.taskId
            ).outerjoin(
                model_mysql_planversion,
                model_mysql_taskinfo.versionId == model_mysql_planversion.versionId
            ).outerjoin(
                model_mysql_planinfo,
                model_mysql_taskinfo.planId == model_mysql_planinfo.planId
            ).filter(
                and_(
                    model_mysql_taskinfo.startTime >= starttime,
                    model_mysql_taskinfo.startTime <= endtime,
                    model_mysql_taskinfo.planId == planid,
                    model_mysql_taskinfo.taskType > 2,
                    model_mysql_planversion.versionId.isnot(None)
                )
            ).group_by(
                model_mysql_taskassign.taskId
            ).having(
                func.count(model_mysql_taskassign.assignId) == func.sum(
                    func.if_(or_(
                        model_mysql_taskassign.status == -1,
                        model_mysql_taskassign.finishTime.isnot(None)
                    ), 1, 0)
                )
            ).order_by(
                func.max(model_mysql_taskassign.finishTime).desc()
            ).limit(
                num
            ).offset(
                (page - 1) * num
            ).all()
        except Exception as e:
            api_logger.error("获取固定时间段内开始执行的历史任务数据失败，表：model_mysql_taskassign，失败原因：" + repr(e))
            return route.error_msgs['msg_db_error']
    else:
        try:
            tasks_count = mysqlpool.session.query(
                model_mysql_taskassign.taskId.label('taskId'),
                func.group_concat(model_mysql_taskassign.status).label('status'),
                func.max(model_mysql_taskassign.finishTime).label('real_endTime'),
                model_mysql_taskinfo.startTime.label('starTime'),
                model_mysql_taskinfo.endTime.label('endTime'),
                model_mysql_taskinfo.taskType.label('taskType'),
                model_mysql_taskinfo.versionId.label('v_id'),
                model_mysql_planversion.versionTitle.label('v_name'),
                model_mysql_taskinfo.planId.label('plan_id'),
                model_mysql_planinfo.planTitle.label('plan_name'),
                model_mysql_planinfo.planType.label('plan_type'),
                model_mysql_taskinfo.taskDescription.label('description'),
                model_mysql_taskinfo.startType.label('startType'),
                model_mysql_taskinfo.endType.label('endType'),
                model_mysql_taskinfo.excuteTimes.label('excuteTimes'),
                model_mysql_taskinfo.errorType.label('errorType'),
                model_mysql_taskinfo.vUser.label('vUser'),
                model_mysql_taskinfo.rampUpPeriod.label('rampUpPeriod')
            ).outerjoin(
                model_mysql_taskinfo,
                model_mysql_taskassign.taskId == model_mysql_taskinfo.taskId
            ).outerjoin(
                model_mysql_planversion,
                model_mysql_taskinfo.versionId == model_mysql_planversion.versionId
            ).outerjoin(
                model_mysql_planinfo,
                model_mysql_taskinfo.planId == model_mysql_planinfo.planId
            ).filter(
                and_(
                    model_mysql_taskinfo.startTime >= starttime,
                    model_mysql_taskinfo.startTime <= endtime,
                    model_mysql_taskinfo.taskType > 2,
                    model_mysql_planversion.versionId.isnot(None)
                )
            ).group_by(
                model_mysql_taskassign.taskId
            ).having(
                func.count(model_mysql_taskassign.assignId) == func.sum(
                    func.if_(or_(
                        model_mysql_taskassign.status == -1,
                        model_mysql_taskassign.finishTime.isnot(None)
                    ), 1, 0)
                )
            ).all()
        except Exception as e:
            api_logger.error("获取固定时间段内开始执行的历史任务总条数失败，表：model_mysql_taskassign，失败原因：" + repr(e))
            return route.error_msgs['msg_db_error']

        try:
            tasks = mysqlpool.session.query(
                model_mysql_taskassign.taskId.label('taskId'),
                func.group_concat(model_mysql_taskassign.status).label('status'),
                func.max(model_mysql_taskassign.finishTime).label('real_endTime'),
                model_mysql_taskinfo.startTime.label('starTime'),
                model_mysql_taskinfo.endTime.label('endTime'),
                model_mysql_taskinfo.taskType.label('taskType'),
                model_mysql_taskinfo.versionId.label('v_id'),
                model_mysql_planversion.versionTitle.label('v_name'),
                model_mysql_taskinfo.planId.label('plan_id'),
                model_mysql_planinfo.planTitle.label('plan_name'),
                model_mysql_planinfo.planType.label('plan_type'),
                model_mysql_taskinfo.taskDescription.label('description'),
                model_mysql_taskinfo.startType.label('startType'),
                model_mysql_taskinfo.endType.label('endType'),
                model_mysql_taskinfo.excuteTimes.label('excuteTimes'),
                model_mysql_taskinfo.errorType.label('errorType'),
                model_mysql_taskinfo.vUser.label('vUser'),
                model_mysql_taskinfo.rampUpPeriod.label('rampUpPeriod')
            ).outerjoin(
                model_mysql_taskinfo,
                model_mysql_taskassign.taskId == model_mysql_taskinfo.taskId
            ).outerjoin(
                model_mysql_planversion,
                model_mysql_taskinfo.versionId == model_mysql_planversion.versionId
            ).outerjoin(
                model_mysql_planinfo,
                model_mysql_taskinfo.planId == model_mysql_planinfo.planId
            ).filter(
                and_(
                    model_mysql_taskinfo.startTime >= starttime,
                    model_mysql_taskinfo.startTime <= endtime,
                    model_mysql_taskinfo.taskType > 2,
                    model_mysql_planversion.versionId.isnot(None)
                )
            ).group_by(
                model_mysql_taskassign.taskId
            ).having(
                func.count(model_mysql_taskassign.assignId) == func.sum(
                    func.if_(or_(
                        model_mysql_taskassign.status == -1,
                        model_mysql_taskassign.finishTime.isnot(None)
                    ), 1, 0)
                )
            ).order_by(
                func.max(model_mysql_taskassign.finishTime).desc()
            ).limit(
                num
            ).offset(
                (page - 1) * num
            ).all()
        except Exception as e:
            api_logger.error("获取固定时间段内开始执行的历史任务数据失败，表：model_mysql_taskassign，失败原因：" + repr(e))
            return route.error_msgs['msg_db_error']

    # 格式化返回值
    response_json['data']['total'] = len(tasks_count)
    for task in tasks:
        response_json['data']['task_list'].append({
            'taskId': task.taskId,
            'status': task.status,
            'startTime': str(task.starTime),
            'endTime': str(task.real_endTime) if task.real_endTime else None,
            'taskType': task.taskType,
            'taskInfo': {
                'v_id': task.v_id,
                'v_name': task.v_name,
                'plan_id': task.plan_id,
                'plan_name': task.plan_name,
                'plan_type': task.plan_type,
                'description': task.description,
                'startType': task.startType,
                'endTime': str(task.endTime) if task.endTime else None,
                'endType': task.endType,
                'excuteTimes': task.excuteTimes,
                'errorType': task.errorType,
                'vUser': task.vUser,
                'rampUpPeriod': task.rampUpPeriod
            }
        })

    return json.dumps(response_json)
