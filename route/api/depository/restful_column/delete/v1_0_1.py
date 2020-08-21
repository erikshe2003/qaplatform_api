# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_case

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作

            判断目录是否存在
            最后返回新增结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_delete_parameter(

    ['id', int, 1, None]
)

def key_column_delete():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据删除成功",
    "data": None
   }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    column_id = flask.request.args['id']


    # 判断目录是否已存在
    try:
        mysql_column_info = model_mysql_case.query.filter(
            model_mysql_case.id == column_id,
            model_mysql_case.type==1
        ).first()
        api_logger.debug("账户基础信息读取成功")
    except Exception as e:
        api_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:

        if mysql_column_info is None:
            return route.error_msgs[201]['msg_no_catalogue']
        elif mysql_column_info.columnId==0:

            return route.error_msgs[201]['msg_column_cannot_operate']
        else:

            mysql_column_info.status = -1
            mysql_column_info.updateUserId=request_user_id
            search_child_column(mysql_column_info.id)
            mysqlpool.session.commit()



    # 最后返回内容
    return response_json

def search_child_column(columnId):

    try:
        mysql_child_info = model_mysql_case.query.filter(
            model_mysql_case.columnId == columnId,model_mysql_case.type==1

        ).all()
        api_logger.debug("账户基础信息读取成功")
    except Exception as e:
        api_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_child_info is None:
            pass
        else:
            for mqti in mysql_child_info:
                mqti.status=-1
                mysqlpool.session.commit()
                search_child_column(mqti.id)
