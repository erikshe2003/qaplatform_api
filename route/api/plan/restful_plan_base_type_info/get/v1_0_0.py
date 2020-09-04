# -*- coding: utf-8 -*-

import route

from handler.log import api_logger

from model.mysql import model_mysql_plantype

"""
    查询测试计划基础类型-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            查询测试计划基础类型数据并返回
"""


@route.check_user
@route.check_token
@route.check_auth
def plan_base_type_info_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "基础测试计划类型数据查询成功",
        "data": []
    }

    # 查询测试计划基础信息，并取出所属者账户id
    try:
        mysql_plan_type_info = model_mysql_plantype.query.filter().all()
    except Exception as e:
        api_logger.error("表model_mysql_plantype读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        for mpti in mysql_plan_type_info:
            response_json["data"].append({
                "typeId": mpti.typeId,
                "typeName": mpti.typeName,
                "typeDescription": mpti.typeDescription
            })

    # 最后返回内容
    return response_json
