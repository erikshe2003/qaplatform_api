# -*- coding: utf-8 -*-

import flask

import route


from handler.log import api_logger

from model.mysql import model_mysql_roleinfo


"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
           查询符合条件的角色
            返回角色清单信息
"""


@route.check_user
@route.check_token
@route.check_auth

def key_projectrole_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data": []
    }


    #查询符合条件的项目id
    try:
        mysql_projectrole_info = model_mysql_roleinfo.query.filter(
            model_mysql_roleinfo.roleIsAdmin ==0,model_mysql_roleinfo.roleStatus==1
        ).all()

    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    if mysql_projectrole_info is None:
        return route.error_msgs[201]['msg_no_data']
    else:

        for mqit in mysql_projectrole_info:
            response_json["data"].append({
                "id": mqit.roleId,
                "name": mqit.roleName,
                "description": mqit.roleDescription,
            })


    # 最后返回内容
    return response_json
