# -*- coding: utf-8 -*-

import flask
import route

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_userinfo

"""
    修改账户所属角色-api路由
    ----校验
    1.校验传参
    2.校验账户是否存在
    3.校验账户操作令牌
    4.校验所操作的账户是否存在
    5.校验所操作的账户所属角色是否是超级管理员
    6.校验所操作的角色是否存在
    7.校验所操作的角色是否是超级管理员角色
    ----操作
    8.修改mysql账户所属角色
    9.修改redis账户所属角色
"""


@route.check_token
@route.check_user
@route.check_auth
@route.check_post_parameter(
    ['user_id', int, 1, None],
    ['role_id', int, 0, None]
)
def user_put():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "",
        "data": {}
    }

    # 取出传入参数值
    requestvalue_userid = flask.request.json["user_id"]
    requestvalue_roleid = flask.request.json["role_id"]

    # 如果传入的roleId为0，则将当前账户的所属角色去除
    if requestvalue_roleid != 0:
        # 6.校验所操作的角色是否存在
        # 7.校验所操作的角色是否是超级管理员角色
        try:
            ri_data = model_mysql_roleinfo.query.filter(
                model_mysql_roleinfo.roleId == requestvalue_roleid
            ).first()
        except Exception as e:
            logmsg = "数据库中角色数据读取失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return route.error_msgs[500]['msg_db_error']
        else:
            if ri_data and ri_data.roleIsAdmin == 0:
                pass
            elif ri_data and ri_data.roleIsAdmin == 1:
                return route.error_msgs[201]['msg_role_is_admin']
            else:
                return route.error_msgs[201]['msg_no_role']

    # 8.修改mysql账户所属角色
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
        u_data.userRoleId = None if requestvalue_roleid == 0 else requestvalue_roleid
        mysqlpool.session.commit()

    # 返回成功信息
    response_json["msg"] = "操作成功"
    # 最后返回内容
    return response_json

