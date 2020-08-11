# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

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
            编辑项目
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['subjectId', int, 1, None],
    ['subjectName', str, 1, 50],
    ['subjectLogoPath', str, 0, 200],
    ['subjectDescription', str, 0, 200]
)

def key_case_put():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据修改成功",
    "data": {
        "id": 1,
        "name": None,
        "logoPath": None,
        "description": None,
        "status": 0
    }
}

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    subject_id = flask.request.json['subjectId']
    subject_name = flask.request.json['subjectName']
    subject_logo_path = flask.request.json['subjectLogoPath']
    subject_description = flask.request.json['subjectDescription']


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
            model_mysql_subject.subjectId == subject_id
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_subject is None:
            return route.error_msgs[201]['msg_no_subject']


    #获取当前id

    """
        插入项目计划数据

    """



    # 如果项目数据有且和传入的一致
    if  mysql_subject.subjectName == subject_name and mysql_subject.subjectLogoPath==subject_logo_path and mysql_subject.subjectDescription==subject_description:
        #
        pass
    # 如果c项目数据有且和传入的一致
    elif mysql_subject.subjectName != subject_name or mysql_subject.subjectLogoPath!=subject_logo_path or mysql_subject.subjectDescription!=subject_description:
        mysql_subject.subjectName = subject_name
        mysql_subject.subjectLogoPath = subject_logo_path
        mysql_subject.subjectDescription = subject_description
        mysqlpool.session.commit()
        # 如果数据无
    else:
        new_subject_info = model_mysql_subject(

            userId=request_user_id,
            subjectName=subject_name,
            subjectLogoPath=subject_logo_path,
            subjectOpenLevel=1,
            subjectDescription=subject_description if subject_description else None,
            subjectStatus=1,

        )
        mysqlpool.session.add(new_subject_info)
        mysqlpool.session.commit()

        # 查询项目更新后信息
    try:
        mysql_subject_info = model_mysql_subject.query.filter(
                model_mysql_subject.subjectId == subject_id
            ).first()
        response_json["data"].update({
                "id": mysql_subject_info.subjectId,
                "name": mysql_subject_info.subjectName,
                "logoPath": mysql_subject_info.subjectLogoPath,
                "description": mysql_subject_info.subjectDescription,
                "status": mysql_subject_info.subjectStatus,
            })


    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_subject_info is None:
            return route.error_msgs[201]['msg_no_subject']




    # 最后返回内容
    return response_json