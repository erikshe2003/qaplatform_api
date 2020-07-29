# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_casePrecondition
from model.mysql import model_mysql_case
from model.mysql import model_mysql_caseFile
from model.mysql import model_mysql_caseStep
from model.mysql import model_mysql_depository
"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断用例是否存在
            返回操作结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_delete_parameter(

    ['ids', str, None, None],
    ['depositoryId', int, 1, None],
    ['columnId', str, None, None]

)

def key_cases_delete():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据删除成功",
    "data": []
   }

    cases_id=[]
    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    depository_id = flask.request.args['depositoryId']
    column_id = flask.request.args['columnId']
    ids = flask.request.args['ids']


    #判断仓库是否存在
    try:
        mysql_depository_info = model_mysql_depository.query.filter(
            model_mysql_depository.id == depository_id
        ).first()
    except Exception as e:
        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_depository_info is None:
            return route.error_msgs[201]['msg_no_depository']
    #判断目录是否存在
    try:
        mysql_column_info = model_mysql_case.query.filter(
            model_mysql_case.columnId == column_id,
            model_mysql_case.status==1,
            model_mysql_case.type==1,
            model_mysql_case.depositoryId == depository_id
        ).first()
    except Exception as e:
        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_column_info is None:
            return route.error_msgs[201]['msg_no_catalogue']

    #根据id批量删除
    if len(ids)==0:
        return route.error_msgs[301]['msg_value_type_error']
    else:
        cases_id = str(ids).split(",")
        for x in cases_id:
            try:
                mysql_case_info = model_mysql_case.query.filter(
                    model_mysql_case.columnId == column_id,
                    model_mysql_case.status == 1,
                    model_mysql_case.type == 2,
                    model_mysql_case.depositoryId == depository_id,
                    model_mysql_case.id==int(x)
                ).first()
            except Exception as e:
                api_logger.error("读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:
                if mysql_case_info is None:
                    pass
                else:
                    mysql_case_info.status=-1
                    mysqlpool.session.commit()

    return response_json