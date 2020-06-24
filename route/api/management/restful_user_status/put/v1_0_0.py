# -*- coding: utf-8 -*-

import flask
import route

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_userinfo

"""
    禁用账户-api路由
    ----校验
    1.校验传参
    2.校验账户是否存在
    3.校验账户操作令牌
    4.校验所操作的账户是否存在
    5.校验所操作的账户所属角色是否是超级管理员
    ----操作
    6.mysq中禁用账户
    7.redis中禁用账户
"""


@route.check_token
@route.check_user
@route.check_auth
@route.check_post_parameter(
    ['user_id', int, 1, None],
    ['status', int, 0, None]
)
def user_status_put():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 取出传入参数值
    requestvalue_userid = flask.request.json["user_id"]
    requestvalue_status = flask.request.json["status"]

    # 4.校验所操作的账户是否存在
    # 5.校验所操作的账户所属角色是否是超级管理员
    try:
        ur_data = mysqlpool.session.query(
            model_mysql_userinfo,
            model_mysql_userinfo.userId,
            model_mysql_userinfo.userStatus,
            model_mysql_roleinfo.roleIsAdmin
        ).join(
            model_mysql_roleinfo,
            model_mysql_roleinfo.roleId == model_mysql_userinfo.userRoleId,
            isouter=True
        ).filter(
            model_mysql_userinfo.userId == requestvalue_userid
        ).first()
    except Exception as e:
        logmsg = "数据库中账号数据读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
    else:
        if ur_data and ur_data.roleIsAdmin in [0, None]:
            pass
        elif ur_data and ur_data.roleIsAdmin == 1:
            return route.error_msgs[201]['msg_user_is_admin']
        elif ur_data and ur_data.userStatus in [-2, 0]:
            return route.error_msgs[201]['msg_user_cannot_operate']
        else:
            return route.error_msgs[201]['msg_no_user']

    # 6.修改mysql账户状态
    try:
        u_data = model_mysql_userinfo.query.filter(
            model_mysql_userinfo.userId == requestvalue_userid
        ).first()
        logmsg = "数据库中账号数据读取成功"
        api_logger.debug(logmsg)
    except Exception as e:
        logmsg = "数据库中账号数据读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
    else:
        u_data.userStatus = requestvalue_status
        mysqlpool.session.commit()

    # 返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json

