# -*- coding: utf-8 -*-

import json
import route

from handler.log import api_logger

from model.mysql import model_mysql_functioninfo


@route.check_user
@route.check_token
@route.check_auth
def role_all_permission_get():
    """
        获取所有角色权限配置清单-api路由
        ----校验
        1.校验传参
        2.校验账户是否存在
        3.校验账户操作令牌
        ----操作
        4.于数据库中查询全量配置清单
    """
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {
            "permission": {
                "all": {}
            }
        }
    }

    # 4.于数据库中查询全量权限配置清单
    try:
        allp_mysql = model_mysql_functioninfo.query.order_by(
            model_mysql_functioninfo.functionType.asc()
        ).all()
    except Exception as e:
        logmsg = "数据库中角色列表读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
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

    # 5.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json

