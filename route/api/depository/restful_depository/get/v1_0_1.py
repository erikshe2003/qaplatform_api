# -*- coding: utf-8 -*-

import flask

import route


from handler.log import api_logger

from model.mysql import model_mysql_depository

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
def key_depository_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data": {
        "id": 0,
        "name": None,
        "description": None,
        "userId": None,
        "baseProjectId": None,
        "createTime": None
        }
    }


    # 取出入参

    depository_id = flask.request.args['id']

    # 查询仓库基础信息
    try:
        mysql_depository_info = model_mysql_depository.query.filter(
            model_mysql_depository.id == depository_id
        ).first()


    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    #判断数据是否存在
    if mysql_depository_info is None:

        return route.error_msgs[201]['msg_no_depository']
    else:

        response_json['data']['id'] = mysql_depository_info.id
        response_json['data']['name'] = mysql_depository_info.name
        response_json['data']['description'] = mysql_depository_info.description
        response_json['data']['userId'] = mysql_depository_info.userId
        response_json['data']['baseProjectId'] = mysql_depository_info.baseProjectId
        response_json['data']['createTime'] = str(mysql_depository_info.createTime)







    # 最后返回内容
    return response_json
