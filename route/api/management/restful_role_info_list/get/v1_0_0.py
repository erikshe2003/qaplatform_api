# -*- coding: utf-8 -*-

import flask
import route

from sqlalchemy import func

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_roleinfo

"""
    获取角色基础信息列表-api路由
"""


@route.check_token
@route.check_user
@route.check_auth
@route.check_get_parameter(
    ['page_num', int, 0, None],
    ['per_page', int, 0, None]
)
def role_info_list_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "",
        "data": {
            "total": 0,
            "role_list": {}
        }
    }

    # 取出传入参数值
    page_num = int(flask.request.args['page_num'])
    per_page = int(flask.request.args['per_page'])

    # 查询角色，包括id/name/canmanage
    # 根据角色id，查询角色下关联的账户，判断角色是否可删除
    try:
        rinfo_mysql = mysqlpool.session.query(
            model_mysql_roleinfo,
            model_mysql_roleinfo.roleId,
            model_mysql_roleinfo.roleName,
            model_mysql_roleinfo.roleIsAdmin
        ).limit(
            # (requestvalue_num - 1) * requestvalue_per,
            per_page
        ).offset(
            (page_num - 1) * per_page
        ).all()
    except Exception as e:
        logmsg = "数据库中角色列表读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
    else:
        # 构造role_list
        for r in rinfo_mysql:
            rsome = {
                "id": r.roleId,
                "name": r.roleName,
                "can_manage": True if r.roleIsAdmin == 0 else False
            }
            response_json["data"]["role_list"][r.roleId] = rsome

    try:
        total_mysql = mysqlpool.session.query(
            func.count(model_mysql_roleinfo.roleId).label(name="roleNum")
        ).first()
        logmsg = "数据库中角色总数读取成功"
        api_logger.debug(logmsg)
    except Exception as e:
        logmsg = "数据库中角色总数读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
    else:
        # 构造total
        response_json["data"]["total"] = total_mysql.roleNum

    # 8.返回成功信息
    response_json["msg"] = "操作成功"
    # 最后返回内容
    return response_json

