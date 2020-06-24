# -*- coding: utf-8 -*-

"""
    逻辑删除个人接口测试计划-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            校验测试计划类型是否存在
            校验是否本人
            逻辑删除测试计划
"""

import flask
import json
import route

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_userinfo


@route.check_user
@route.check_token
@route.check_auth
@route.check_delete_parameter(
    ['planId', int, 1, None]
)
def plan_delete():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {}
    }

    user_id = None
    # 取出必传入参
    mail_address = flask.request.headers['Mail']
    plan_id = int(flask.request.args['planId'])

    # 查询mysql中账户信息，并取出账户id
    try:
        mysql_userinfo = model_mysql_userinfo.query.filter(
            model_mysql_userinfo.userEmail == mail_address
        ).first()
        api_logger.debug(mail_address + "的账户基础信息读取成功")
    except Exception as e:
        api_logger.error(mail_address + "的账户基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_userinfo is None:
            return route.error_msgs[201]['msg_no_user']
        else:
            user_id = mysql_userinfo.userId

    # 逻辑删除测试计划
    try:
        mysql_planinfo = model_mysql_planinfo.query.filter(
            model_mysql_planinfo.planId == plan_id
        ).first()
    except Exception as e:
        api_logger.error(mail_address + "的测试计划信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        # 只有计划本人才有权限删除该计划
        if user_id == mysql_planinfo.ownerId and mysql_planinfo:
            mysql_planinfo.status = -1
            try:
                mysqlpool.session.commit()
            except Exception as e:
                api_logger.error("个人接口测试计划删除失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
        elif user_id != mysql_planinfo.ownerId:
            return route.error_msgs[201]['msg_plan_user_error']
        else:
            return route.error_msgs[201]['msg_no_plan']

    # 最后返回内容
    return response_json
