# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_catalogue
from model.mysql import model_mysql_subject
"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断测试目录是否存在
            新增目录
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(

    ['catalogueName', str, 1, 255],
    ['subjectId', int, 1, None]
)

def key_catalogue_post():
    # 初始化返回内容
    response_json ={
    "code": 200,
    "msg": "目录新增成功",
    "data": None
}

    # 取出必传入参

    catalogue_name = flask.request.json['catalogueName']
    subject_id = flask.request.json['subjectId']


    # subject_id判断关联的项目是否存在
    try:
        mysql_subjectinfo = model_mysql_subject.query.filter(
            model_mysql_subject.subjectId == subject_id
        ).first()
        api_logger.debug("项目信息读取成功")
    except Exception as e:
        api_logger.error("项目信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_subjectinfo is None:
            return route.error_msgs[201]['msg_no_subject']

    # 查询名称是否存在
    try:
        mysql_catalogue= model_mysql_catalogue.query.filter(
            model_mysql_catalogue.catalogueName == catalogue_name
        ).first()
    except Exception as e:
        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_catalogue is None:
            pass
        else:
            return route.error_msgs[201]['msg_exit_catalogue']
    #获取当前id

    """
        插入数据

    """
    new_catalogue_info = model_mysql_catalogue(

        subjectId=subject_id,
        catalogueName=catalogue_name,
        catalogueStatus=1,

    )
    mysqlpool.session.add(new_catalogue_info)
    mysqlpool.session.commit()

    # 最后返回内容
    return response_json