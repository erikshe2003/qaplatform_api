# -*- coding: utf-8 -*-

import flask
import route

from sqlalchemy import func

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_userinfo


# 按关键字模糊搜索角色-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验账户操作令牌
# ----操作
# 4.查询角色，包括id/name/addtime/updatetime/canmanage
# 5.根据角色id，查询角色下关联的账户，判断角色是否可删除
# 6.根据角色isAdmin，判断角色是否可管理
# 7.查询角色的总数
@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['key_word', str, 0, 100]
)
def role_get():
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
    requestvalue_keyword = flask.request.args["key_word"]

    # 4.查询角色，包括id/name/addtime/updatetime/canmanage
    # 5.根据角色id，查询角色下关联的账户，判断角色是否可删除
    try:
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
            model_mysql_roleinfo.roleName.like('%' + requestvalue_keyword + '%')
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
            model_mysql_roleinfo,
            func.count(model_mysql_roleinfo.roleId).label("roleNum"),
        ).first()
    except Exception as e:
        logmsg = "数据库中角色列表读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 构造total
        response_json["data"]["total"] = total_mysql.roleNum
    # 8.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json