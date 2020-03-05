# -*- coding: utf-8 -*-

import flask
import json
import route

from sqlalchemy import and_

from handler.log import api_logger
from handler.pool import mysqlpool
from handler.socket.task import kill_task

from route.api.task import api_task

from model.mysql import model_mysql_userinfo
from model.mysql import model_mysql_taskinfo
from model.mysql import model_mysql_taskassign
from model.mysql import model_mysql_workerinfo

from model.redis import model_redis_userinfo

"""
    强行停止测试任务
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            检查测试计划以及测试版本是否存在
            新增调试任务
            将测试任务数据打包发送给执行应用
"""


@api_task.route('/stopTestTask.json', methods=['post'])
@route.check_token
@route.check_user
@route.check_auth
@route.check_post_parameter(
    ['taskId', int, 1, None]
)
def stop_test_task():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {}
    }

    # 取出taskId
    mail_address = flask.request.headers['Mail']
    task_id = flask.request.json['taskId']

    # 根据mail_address在缓存中查找账户id
    redis_user_info = model_redis_userinfo.query(user_email=mail_address)
    # 如果缓存中没查到，则查询mysql
    if redis_user_info is None:
        try:
            mysql_user_info = model_mysql_userinfo.query.filter(
                model_mysql_userinfo.userEmail == mail_address
            ).first()
            api_logger.debug(mail_address + "的账户基础信息读取成功")
        except Exception as e:
            api_logger.error(mail_address + "的账户基础信息读取失败，失败原因：" + repr(e))
            return route.error_msgs['msg_db_error']
        else:
            if mysql_user_info is None:
                return route.error_msgs['msg_no_user']
            else:
                user_id = mysql_user_info.userId
    else:
        # 格式化缓存中基础信息内容
        try:
            redis_user_info_json = json.loads(redis_user_info.decode("utf8"))
            api_logger.debug(mail_address + "的缓存账户数据json格式化成功")
        except Exception as e:
            api_logger.error(mail_address + "的缓存账户数据json格式化失败，失败原因：" + repr(e))
            return route.error_msgs['msg_json_format_fail']
        else:
            user_id = redis_user_info_json['userId']

    # 根据user_id/task_id查询测试任务记录
    try:
        the_task_info = model_mysql_taskinfo.query.filter(
            and_(
                model_mysql_taskinfo.taskId == task_id,
                model_mysql_taskinfo.createUser == user_id
            )
        ).first()
    except Exception as e:
        api_logger.debug("测试任务数据读取失败，失败原因：" + repr(e))
        return route.error_msgs['msg_db_error']
    else:
        if not the_task_info:
            return route.error_msgs['msg_no_test_task']
        else:
            # 根据taskId来查询测试任务下发记录
            try:
                task_assign_data = mysqlpool.session.query(
                    model_mysql_taskassign.assignId,
                    model_mysql_taskassign.taskId,
                    model_mysql_taskassign.workerId,
                    model_mysql_workerinfo.ip,
                    model_mysql_workerinfo.port
                ).outerjoin(
                    model_mysql_workerinfo,
                    model_mysql_taskassign.workerId == model_mysql_workerinfo.workerId
                ).filter(
                    model_mysql_taskassign.taskId == task_id,
                    model_mysql_taskassign.status > -1,
                    model_mysql_taskassign.finishTime == None
                ).all()
            except Exception as e:
                api_logger.debug(mail_address + "的临时测试计划版本读取失败，失败原因：" + repr(e))
                return route.error_msgs['msg_db_error']
            else:
                # 下发终止测试任务的socket请求
                kill_task(task_assign_data)

    return json.dumps(response_json)
