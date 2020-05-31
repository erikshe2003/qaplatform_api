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
    ['key_word', str, 0, 100],
    ['status', int, -100, 100],
    ['role_id', int, 0, None],
    ['page_num', int, 1, None],
    ['per_page', int, 1, None]
)
def user_get():
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
    requestvalue_keyword = flask.request.args["key_word"]
    requestvalue_status = int(flask.request.args["status"])
    requestvalue_roleid = int(flask.request.args["role_id"])
    requestvalue_num = int(flask.request.args["page_num"])
    requestvalue_per = int(flask.request.args["per_page"])

    # 4.join查询包含所属角色的账户基础信息，
    # 包括id/nickname/email/status/roleid/rolename/registertime/candelete/canmanage
    # 需添加filter条件
    # keyword模糊搜索userEmail
    # status为10则不搜索，为其他则精确匹配
    # role_id为0则不搜索，为其他则精确匹配
    try:
        uinfo_mysql = mysqlpool.session.query(
            model_mysql_userinfo,
            model_mysql_userinfo.userId,
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
        ).filter(
            model_mysql_userinfo.userEmail.like('%' + requestvalue_keyword + '%'),
        )
        if requestvalue_status == 10:
            pass
        else:
            uinfo_mysql = uinfo_mysql.filter(
                model_mysql_userinfo.userStatus == requestvalue_status
            )
        if requestvalue_roleid == 0:
            pass
        else:
            uinfo_mysql = uinfo_mysql.filter(
                model_mysql_userinfo.userRoleId == requestvalue_roleid
            )
        uinfo_mysql = uinfo_mysql.limit(
            # (requestvalue_num - 1) * requestvalue_per,
            requestvalue_per
        ).offset(
            (requestvalue_num - 1) * requestvalue_per
        ).all()
    except Exception as e:
        logmsg = "数据库中账号列表读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 构造user_list
        for u in uinfo_mysql:
            usome = {
                "id": u.userId,
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

    try:
        total_mysql = mysqlpool.session.query(
            func.count(model_mysql_userinfo.userId).label(name="userNum")
        ).first()
        logmsg = "数据库中账号总数读取成功"
        api_logger.debug(logmsg)
    except Exception as e:
        logmsg = "数据库中账号总数读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 构造total
        response_json["data"]["total"] = total_mysql.userNum

    # 8.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json
