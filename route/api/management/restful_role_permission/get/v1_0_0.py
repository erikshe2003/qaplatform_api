# -*- coding: utf-8 -*-

import flask
import route

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_functioninfo
from model.mysql import model_mysql_rolepermission


# 获取角色权限配置清单-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验账户操作令牌
# ----操作
# 4.于数据库中查询角色配置清单
# 5.于数据库中查询全量配置清单
@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['role_id', int, 1, None]
)
def role_permission_get():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {
            "permission": {
                "all": {},
                "role": {}
            }
        }
    }

    # 取出传入参数值
    requestvalue_roleid = int(flask.request.args["role_id"])

    # 4.于数据库中查询角色配置清单
    try:
        rolep_mysql = mysqlpool.session.query(
            model_mysql_rolepermission,
            model_mysql_functioninfo.functionId,
            model_mysql_functioninfo.functionAlias,
            model_mysql_functioninfo.functionDescription,
            model_mysql_functioninfo.functionType,
            model_mysql_rolepermission.hasPermission,
            model_mysql_functioninfo.rootId
        ).join(
            model_mysql_functioninfo,
            model_mysql_rolepermission.functionId == model_mysql_functioninfo.functionId
        ).filter(
            model_mysql_rolepermission.roleId == requestvalue_roleid,
            model_mysql_rolepermission.hasPermission == 1
        ).order_by(
            model_mysql_functioninfo.functionType.asc()
        ).all()
    except Exception as e:
        logmsg = "数据库中角色列表读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
    else:
        # 构造角色权限配置清单
        for rp in rolep_mysql:
            # 如果此行记录为page，则记录
            if rp.functionType == 1:
                response_json["data"]["permission"]["role"][rp.functionId] = {
                    "id": rp.functionId,
                    "alias": rp.functionAlias,
                    "component": {}
                }
            else:
                # 如果为组件，则根据rootId判断append至哪个page的component中
                response_json["data"]["permission"]["role"][rp.rootId]['component'][rp.functionId] = {
                    "id": rp.functionId,
                    "alias": rp.functionAlias,
                }

    # 5.于数据库中查询全量权限配置清单
    try:
        allp_mysql = model_mysql_functioninfo.query.order_by(
            model_mysql_functioninfo.functionType.asc()
        ).all()
    except Exception as e:
        logmsg = "数据库中角色列表读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
    else:
        # 构造角色权限配置清单
        for ap in allp_mysql:
            # 如果此行记录为page，则记录
            if ap.functionType == 1:
                response_json["data"]["permission"]["all"][ap.functionId] = {
                    "id": ap.functionId,
                    "name": ap.functionName,
                    "alias": ap.functionAlias,
                    "description": ap.functionDescription,
                    "component": {}
                }
            else:
                # 如果为组件，则根据rootId判断添加至哪个page的component中
                response_json["data"]["permission"]["all"][ap.rootId]['component'][ap.functionId] = {
                    "id": ap.functionId,
                    "name": ap.functionName,
                    "alias": ap.functionAlias,
                    "description": ap.functionDescription
                }

    # 8.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json
