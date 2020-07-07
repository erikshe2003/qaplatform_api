# -*- coding: utf-8 -*-

import flask

import route


from handler.log import api_logger

from model.mysql import model_mysql_catalogue

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断请求是否合法
            返回信息
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['subjectId', int, 1, None],
    ['catalogueId', int, 1, None]
)
def key_catalogue_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data": {
        "catalogueId": 1,
        "catalogueName": None,
        "createTime": None,
        "updateTime": None
    }
}


    # 取出入参

    catalogue_id = flask.request.args['catalogueId']
    subject_id = flask.request.args['subjectId']


    # 查询项目基础信息，并取出所属者账户id
    try:
        mysql_catalogue_info = model_mysql_catalogue.query.filter(
            model_mysql_catalogue.catalogueId == catalogue_id
        ).first()

    except Exception as e:
        api_logger.error("model_mysql_subjectinfo数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    if mysql_catalogue_info is None:
        return route.error_msgs[201]['msg_no_catalogue']
    elif mysql_catalogue_info.subjectId!=int(subject_id):
        return route.error_msgs[201]['msg_data_error']
    else:
        response_json['data']['catalogueId'] = mysql_catalogue_info.catalogueId
        response_json['data']['catalogueName'] = mysql_catalogue_info.catalogueName
        response_json['data']['createTime'] = str(mysql_catalogue_info.catalogueCreateTime)
        response_json['data']['updateTime'] = str(mysql_catalogue_info.catalogueUpdateTime)


    # 根据项目状态以及操作者id/计划拥有者id判断返回内容

    if mysql_catalogue_info.catalogueStatus in (1, 2):
            pass
    else:
            return route.error_msgs[201]['msg_no_catalogue']



    # 最后返回内容
    return response_json
