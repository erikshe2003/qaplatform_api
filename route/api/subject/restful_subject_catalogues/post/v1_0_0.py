# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

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
            合并目录，即归档
            目录提供归档功能，即非全部用例目录下的所有内容整合至全部用例下
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(

    ['catalogue', int, 1, None],
    ['subjectId', int, 1, None]

)

def key_catalogues_post():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "目录归档成功",
    "data": None
}

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    subject_name = flask.request.json['subjectName']
    subject_logo_path = flask.request.json['subjectLogoPath']
    subject_description = flask.request.json['subjectDescription']
    subject_open_level = flask.request.json['subjectOpenLevel']

    # 判断user_id是否存在
    try:
        mysql_userinfo = model_mysql_subject.query.filter(
            model_mysql_subject.userId == request_user_id
        ).first()
        api_logger.debug("账户基础信息读取成功")
    except Exception as e:
        api_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_userinfo is None:
            return route.error_msgs[201]['msg_no_user']

    # 查询项目名称是否存在
    try:
        mysql_subject = model_mysql_subject.query.filter(
            model_mysql_subject.subjectName == subject_name
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_subject is None:
            pass
        else:
            return route.error_msgs[201]['msg_exit_subject']
    #获取当前id

    """
        插入项目计划数据

    """
    new_subject_info = model_mysql_subject(

        userId=request_user_id,
        subjectName=subject_name,
        subjectLogoPath=subject_logo_path,
        subjectOpenLevel=subject_open_level,
        subjectDescription=subject_description if subject_description else None,
        subjectStatus=1,

    )
    mysqlpool.session.add(new_subject_info)
    mysqlpool.session.commit()

    # 最后返回内容
    return response_json