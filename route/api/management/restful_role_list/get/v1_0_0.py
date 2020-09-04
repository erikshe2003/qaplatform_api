# -*- coding: utf-8 -*-

import flask
import route

from sqlalchemy import func

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_userinfo


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['page_num', int, 1, None],
    ['per_page', int, 1, None],
    ['key_word', str, 0, 100]
)
def role_list_get():
    """
        获取角色列表-api路由
        ----校验
        1.校验传参
        2.校验账户是否存在
        3.校验账户操作令牌
        //4.校验账户所属角色是否具有后端权限//
        ----操作
        4.查询角色，包括id/name/addtime/updatetime/canmanage
        5.根据角色id，查询角色下关联的账户，判断角色是否可删除
        6.根据角色isAdmin，判断角色是否可管理
        7.查询角色的总数
    """
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "",
        "data": {
            "total": 0,
            "role_list": {

            }
        }
    }

    # 取出传入参数值
    requestvalue_num = int(flask.request.args["page_num"])
    requestvalue_per = int(flask.request.args["per_page"])
    requestvalue_key = flask.request.args["key_word"]

    # 4.查询角色，包括id/name/addtime/updatetime/canmanage
    # 5.根据角色id，查询角色下关联的账户，判断角色是否可删除
    try:
        rinfo_mysql_query = mysqlpool.session.query(
            model_mysql_roleinfo,
            model_mysql_roleinfo.roleId,
            model_mysql_roleinfo.roleName,
            model_mysql_roleinfo.roleDescription,
            model_mysql_roleinfo.roleIsAdmin,
            model_mysql_roleinfo.roleAddTime,
            model_mysql_roleinfo.roleUpdateTime,
            func.count(model_mysql_userinfo.userId).label("userNum")
        ).join(
            model_mysql_userinfo,
            model_mysql_roleinfo.roleId == model_mysql_userinfo.userRoleId,
            isouter=True
        ).group_by(
            model_mysql_roleinfo.roleId
        )
        if requestvalue_key == '':
            rinfo_mysql = rinfo_mysql_query.limit(
                # (requestvalue_num - 1) * requestvalue_per,
                requestvalue_per
            ).offset(
                (requestvalue_num - 1) * requestvalue_per
            ).all()
        else:
            rinfo_mysql = rinfo_mysql_query.filter(
                model_mysql_roleinfo.roleName.like('%' + requestvalue_key + '%')
            ).limit(
                # (requestvalue_num - 1) * requestvalue_per,
                requestvalue_per
            ).offset(
                (requestvalue_num - 1) * requestvalue_per
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
                "description": r.roleDescription,
                "can_manage": True if r.roleIsAdmin == 0 else False,
                "can_delete": True if r.userNum == 0 else False,
                "add_time": str(r.roleAddTime),
                "update_time": str(r.roleUpdateTime)
            }
            response_json["data"]["role_list"][r.roleId] = rsome

    try:
        total_mysql_query = mysqlpool.session.query(
            func.count(model_mysql_roleinfo.roleId).label(name="roleNum")
        )
        if requestvalue_key == '':
            total_mysql = total_mysql_query.first()
        else:
            total_mysql = total_mysql_query.filter(
                model_mysql_roleinfo.roleName.like('%' + requestvalue_key + '%')
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
