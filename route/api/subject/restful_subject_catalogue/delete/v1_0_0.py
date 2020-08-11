# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool
from handler.log import api_logger

from model.mysql import model_mysql_subject
from model.mysql import model_mysql_catalogue
"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断是否存在
            删除信息
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_delete_parameter(
    ['catalogueId', int, 1, None],
    ['subjectId', int, 1, None]
)
def key_catalogue_delete():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据删除成功",
    "data": None
    }


    # 取出入参
    catalogue_id = flask.request.args['catalogueId']
    subject_id = flask.request.args['subjectId']



    # # 判断subject_id是否存在
    try:
        mysql_subjectinfo = model_mysql_subject.query.filter(
            model_mysql_subject.subjectId == subject_id
        ).first()
        api_logger.debug("基础信息读取成功")
    except Exception as e:
        api_logger.error("基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_subjectinfo is None:
            return route.error_msgs[201]['msg_no_subject']

    # 查询 catalogue_id是否存在,存在即逻辑删除
    try:
        mysql_catalogue = model_mysql_catalogue.query.filter(
            model_mysql_catalogue.catalogueId == catalogue_id
        ).first()
        mysql_catalogue.catalogueStatus=-1
        mysqlpool.session.commit()

        if mysql_catalogue.subjectId==int(subject_id):
            mysql_catalogue.catalogueStatus=-1
            mysqlpool.session.commit()
        else:
            return route.error_msgs[201]['msg_data_error']


    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']


    # 最后返回内容
    return response_json
