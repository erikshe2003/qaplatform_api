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
            判断测试目录是否存在
            编辑目录
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['subjectId', int, 1, None],
    ['catalogueId', int, 1, None],
    ['catalogueName', str, 1, 255]
)

def key_catalogue_put():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "目录修改成功",
    "data": None
}

    # 取出必传入参

    subject_id = flask.request.json['subjectId']
    catalogue_id = flask.request.json['catalogueId']
    catalogue_name = flask.request.json['catalogueName']


    # 判断subject_id是否存在
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

    # 查询名称是否存在
    try:
        mysql_catalogue = model_mysql_catalogue.query.filter(
            model_mysql_catalogue.catalogueId == catalogue_id
        ).first()
    except Exception as e:
        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_catalogue is None:
            return route.error_msgs[201]['msg_no_subject']


    #获取当前id

    """
        插入项目计划数据

    """



    # 如果数据有且和传入的一致
    if  mysql_catalogue.subjectId == subject_id and mysql_catalogue.catalogueId==catalogue_id and mysql_catalogue.catalogueName==catalogue_name:
        #
        pass
    # 如果数据有且和传入不一致
    elif mysql_catalogue.subjectId != subject_id or mysql_catalogue.catalogueName!=catalogue_name:
        mysql_catalogue.subjectId = subject_id
        mysql_catalogue.catalogueName = catalogue_name

        mysqlpool.session.commit()
        # 如果数据无
    else:
        return route.error_msgs[201]['msg_illegal_format']



    # 最后返回内容
    return response_json