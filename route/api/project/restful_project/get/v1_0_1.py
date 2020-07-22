# -*- coding: utf-8 -*-

import flask

import route


from handler.log import api_logger

from model.mysql import model_mysql_project
from model.mysql import model_mysql_projectMember

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断测试仓库是否存在
            返回测试仓库基础信息
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['id', int, 1, None]
)
def key_project_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data": {
        "id": 0,
        "name": None,
        "description": None,
        "coverOssPath": None,
        "userId": None,
        "depositoryId": None,
        "originalProjectId": None,
        "createTime": None,
        "members":[]
        }
    }


    # 取出入参

    project_id = flask.request.args['id']

    # 查询项目基础信息
    try:
        mysql_project_info = model_mysql_project.query.filter(
            model_mysql_project.id == project_id,model_mysql_project.status==1
        ).first()


    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    #判断数据是否存在
    if mysql_project_info is None:

        return route.error_msgs[201]['msg_no_project']
    else:

        response_json['data']['id'] = mysql_project_info.id
        response_json['data']['name'] = mysql_project_info.name
        response_json['data']['description'] = mysql_project_info.description
        response_json['data']['coverOssPath'] = mysql_project_info.coverOssPath
        response_json['data']['userId'] = mysql_project_info.userId
        response_json['data']['depositoryId'] = mysql_project_info.depositoryId
        response_json['data']['createTime'] = str(mysql_project_info.createTime)
    #查看项目成员

    try:
        mysql_projectMember_info = model_mysql_projectMember.query.filter(
            model_mysql_projectMember.projectId == project_id,model_mysql_projectMember.status==1
        ).all()


    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    if mysql_projectMember_info is None:
        pass
    else:
        for mpti in mysql_projectMember_info:

            response_json['data']['members'].append({
                "id": mpti.id,
                "userId": mpti.userId,
                "type": str(mpti.type),
                "createTime": str(mpti.createTime)
            })


    # 最后返回内容
    return response_json
