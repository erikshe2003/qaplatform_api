# -*- coding: utf-8 -*-

import flask
import route

from sqlalchemy import func

from handler.api.error import ApiError
from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_userinfo


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['page_num', int, 1, None],
    ['per_page', int, 1, None]
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
        "error_code": 200,
        "error_msg": "",
        "data": {
            "total": 0,
            "role_list": {

            }
        }
    }

    # 取出传入参数值
    requestvalue_num = int(flask.request.args["page_num"])
    requestvalue_per = int(flask.request.args["per_page"])
    requestvalue_key = None

    # keywork非必填
    if "key_word" not in flask.request.args:
        pass
    else:
        if type(flask.request.args["key_word"]) is not str or len(flask.request.args["key_word"]) > 100:
            return ApiError.requestfail_value("key_word")
        requestvalue_key = flask.request.args["key_word"]

    # 4.查询角色，包括id/name/addtime/updatetime/canmanage
    # 5.根据角色id，查询角色下关联的账户，判断角色是否可删除
    try:
        if not requestvalue_key:
            rinfo_mysql = mysqlpool.session.query(
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
            ).limit(
                # (requestvalue_num - 1) * requestvalue_per,
                requestvalue_per
            ).offset(
                (requestvalue_num - 1) * requestvalue_per
            ).all()
        else:
            rinfo_mysql = mysqlpool.session.query(
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
            ).filter(
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
        total_mysql = mysqlpool.session.query(
            func.count(model_mysql_roleinfo.roleId).label(name="roleNum")
        ).first()
        logmsg = "数据库中角色总数读取成功"
        api_logger.debug(logmsg)
    except Exception as e:
        logmsg = "数据库中角色总数读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 构造total
        response_json["data"]["total"] = total_mysql.roleNum

    # 8.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json
