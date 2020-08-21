# -*- coding: utf-8 -*-

import flask

import route


from handler.log import api_logger

from model.mysql import model_mysql_project

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            根据项目获取仓库id
            根据仓库id获取关联的项目
            返回项目清单信息
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ["id",int,1,None]
)

def key_projectlist_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data": []
    }

    project_id=flask.request.args['id']
    print(project_id)

    #查询符合条件的项目并获得仓库id
    try:
        mysql_project_info = model_mysql_project.query.filter(
            model_mysql_project.id == project_id,
            model_mysql_project.status != -1
        ).first()

    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    if mysql_project_info is None:
        print(111)
        return route.error_msgs[201]['msg_no_project']
    else:
        depository_Id=mysql_project_info.depositoryId

    #查询符合条件的项目
    try:
        mysql_projects_info = model_mysql_project.query.filter(
            model_mysql_project.depositoryId ==depository_Id,
            model_mysql_project.status != -1,
            model_mysql_project.id !=project_id
        ).all()

    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    if mysql_projects_info is None:
        print(2222)
        return route.error_msgs[201]['msg_no_project']
    else:
        for mqti in mysql_projects_info:
            response_json["data"].append({
                "id":mqti.id,
                "name":mqti.id,
                "decription":mqti.description,
                "coverOssPath":mqti.coverOssPath
            })


    # 最后返回内容
    return response_json
