# -*- coding: utf-8 -*-

import flask
import route

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_userinfo

"""
    删除（逻辑删除）/恢复账户-api路由
    ----校验
    1.校验传参
    2.校验账户是否存在
    3.校验账户操作令牌
    4.校验所操作的账户是否存在
    5.校验所操作的账户所属角色是否是超级管理员
    ----操作
    6.mysq中删除账户
    7.redis中删除账户
"""


@route.check_token
@route.check_user
@route.check_auth
@route.check_delete_parameter(
    ['user_id', int, 1, None],
    ['status', int, 0, None]
)
def user_delete():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 取出传入参数值
    requestvalue_userid = int(flask.request.args["user_id"])
    requestvalue_status = int(flask.request.args["status"])

    # 4.校验所操作的账户是否存在
    # 5.校验所操作的账户所属角色是否是超级管理员
    try:
        ur_data = mysqlpool.session.query(
            model_mysql_userinfo,
            model_mysql_userinfo.userId,
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
            return route.error_msgs[201]['msg_role_is_admin']
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
        """
            邮箱存在-删除-删除
            邮箱不存在-删除-删除
            邮箱存在-恢复-正常
            邮箱不存在-恢复-未激活
        """
        if u_data.userEmail:
            u_data.userStatus = requestvalue_status
        else:
            u_data.userStatus = 0
        mysqlpool.session.commit()

    # 返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json

