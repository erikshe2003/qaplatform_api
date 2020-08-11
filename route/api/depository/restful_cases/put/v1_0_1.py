# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger


from model.mysql import model_mysql_case
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
@route.check_post_parameter(

    ['ids', str, None, None],
    ['depositoryId', int, 1, None],
    ['fromColumnId', int, 1, None],
    ['toColumnId', int, 1, None]

)

def key_cases_put():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据移动成功",
    "data": []
   }

    cases_id=[]
    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    depository_id = flask.request.json['depositoryId']
    from_column_id = flask.request.json['fromColumnId']
    to_column_id = flask.request.json['toColumnId']
    ids = flask.request.json['ids']


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
    #判断from目录是否存在
    try:
        mysql_column_info = model_mysql_case.query.filter(
            model_mysql_case.columnId == from_column_id,
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
    #判断to目录是否存在
    try:
        mysql_column_info = model_mysql_case.query.filter(
            model_mysql_case.columnId == to_column_id,
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


    #根据目标case中最大index
    try:
        mysql_max_info = model_mysql_case.query.filter(
            model_mysql_case.columnId == to_column_id,
            model_mysql_case.status == 1,
            model_mysql_case.type == 2,
            model_mysql_case.depositoryId == depository_id,
        ).order_by(model_mysql_case.index.desc()).first()

    except Exception as e:
        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_max_info is None:
            index=0
        else:
            index=mysql_max_info.index

    #根据出入的ids获取用例信息，移入目录中的case排在后面
    if len(ids)==0:
        return route.error_msgs[301]['msg_value_type_error']
    else:
        cases_id = str(ids).split(",")
        try:
            mysql_cases_info = model_mysql_case.query.filter(
                model_mysql_case.columnId == from_column_id,
                model_mysql_case.status == 1,
                model_mysql_case.type == 2,
                model_mysql_case.depositoryId == depository_id,
                model_mysql_case.id.in_(cases_id)
            ).order_by(model_mysql_case.index).all()

        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_cases_info is None:
                return route.error_msgs[201]['msg_no_case']
            else:
                for x in mysql_cases_info:
                    x.columnId=to_column_id
                    x.index=index+1

                    mysqlpool.session.commit()

                    index+=1
    #存在优化空间index会越拖越大

    return response_json