# -*- coding: utf-8 -*-

import flask
import route

from sqlalchemy import func

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_userinfo


"""
    获取包含账户基础信息的列表-api路由
    ----校验
    1.校验传参
    2.校验账户是否存在
    3.校验账户操作令牌
    ----操作
    4.join查询包含所属角色的账户基础信息，
    包括id/nickname/email/status/roleid/rolename/registertime/candelete/canmanage
"""
@route.check_token
@route.check_user
@route.check_auth
@route.check_get_parameter(
    ['page_num', int, 0, None],
    ['per_page', int, 0, None]
)
def user_list_get():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {
            "total": 0,
            "user_list": {}
        }
    }

    # 取出传入参数值
    requestvalue_num = int(flask.request.args["page_num"])
    requestvalue_per = int(flask.request.args["per_page"])

    # 4.join查询包含所属角色的账户基础信息，
    # 包括id/nickname/email/status/roleid/rolename/registertime/candelete/canmanage
    # 所属角色为超级管理员的账号无法删除且无法管理
    # 非超级管理员角色的账号可删除且可管理
    # 删除为逻辑删除
    try:
        uinfo_mysql = mysqlpool.session.query(
            model_mysql_userinfo,
            model_mysql_userinfo.userId,
            model_mysql_userinfo.userLoginName,
            model_mysql_userinfo.userNickName,
            model_mysql_userinfo.userEmail,
            model_mysql_userinfo.userStatus,
            model_mysql_userinfo.userRoleId,
            model_mysql_roleinfo.roleName,
            model_mysql_userinfo.userRegisterTime,
            model_mysql_roleinfo.roleIsAdmin
        ).join(
            model_mysql_roleinfo,
            model_mysql_roleinfo.roleId == model_mysql_userinfo.userRoleId,
            isouter=True
        )
    except Exception as e:
        logmsg = "数据库中账号列表读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
    else:
        # 构造total
        response_json["data"]["total"] = uinfo_mysql.count()
        # 构造user_list
        uinfo_mysql = uinfo_mysql.limit(
            # (requestvalue_num - 1) * requestvalue_per,
            requestvalue_per
        ).offset(
            (requestvalue_num - 1) * requestvalue_per
        ).all()
        for u in uinfo_mysql:
            usome = {
                "id": u.userId,
                "login_name": u.userLoginName,
                "nick_name": u.userNickName,
                "email": u.userEmail,
                "status": u.userStatus,
                "role_id": u.userRoleId,
                "role_name": u.roleName,
                "register_time": str(u.userRegisterTime) if u.userRegisterTime else u.userRegisterTime,
                "can_manage": False if u.roleIsAdmin else True,
                "can_delete": False if u.roleIsAdmin else True
            }
            response_json["data"]["user_list"][u.userId] = usome

    # 8.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json

