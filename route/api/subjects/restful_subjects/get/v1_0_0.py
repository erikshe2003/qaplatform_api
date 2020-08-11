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

def key_subjects_get():
    # 初始化返回内容
    response_json ={
    "code": 200,
    "msg": "数据获取成功",
    "data": []
    }

    # 查询项目信息基础信息
    try:
        mysql_subjects_info = model_mysql_subject.query.filter().all()
    except Exception as e:
        api_logger.error("表model_mysql_subject读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        for mpti in mysql_subjects_info:
            response_json["data"].append({
                "id": mpti.subjectId,
                "name": mpti.subjectName,
                "logoPath": mpti.subjectLogoPath,
                "description": mpti.subjectDescription,
                "status": mpti.subjectStatus,
            })

    # 最后返回内容
    return response_json