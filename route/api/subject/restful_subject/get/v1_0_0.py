# -*- coding: utf-8 -*-

import flask

import route


from handler.log import api_logger

from model.mysql import model_mysql_subject

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断测试项目是否存在
            返回测试项目基础信息
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['subjectId', int, 1, None]
)
def key_subject_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data": {
        "id": 0,
        "name": None,
        "logoPath": None,
        "description": None,
        "status": 1
        }
    }

    subject_user_id = None
    # 取出入参
    request_user_id = flask.request.headers['UserId']
    subject_id = flask.request.args['subjectId']

    # 查询项目基础信息，并取出所属者账户id
    try:
        mysql_subject_info = model_mysql_subject.query.filter(
            model_mysql_subject.subjectId == subject_id
        ).first()
    except Exception as e:
        api_logger.error("model_mysql_subjectinfo数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_subject_info is None:
            return route.error_msgs[201]['msg_no_subject']
        else:
            subject_user_id = mysql_subject_info.userId
            response_json['data']['id'] = mysql_subject_info.subjectId
            response_json['data']['name'] = mysql_subject_info.subjectName
            response_json['data']['logoPath'] = mysql_subject_info.subjectLogoPath
            response_json['data']['description'] = mysql_subject_info.subjectDescription
            response_json['data']['status'] = mysql_subject_info.subjectStatus


    # 根据项目状态以及操作者id/计划拥有者id判断返回内容
    if request_user_id == subject_user_id:
        pass
    else:
        if mysql_subject_info.subjectStatus in (1, 2):
            pass
        else:
            return route.error_msgs[201]['msg_no_subject']



    # 最后返回内容
    return response_json
