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
            先判断仓库是否有效
            再判断关联目录是否有效
            然后判断目录是否存在
            最后返回新增结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(

    ['name', str, 1, 200],
    ['columnId', int, 1, None],
    ['depositoryId', int, 1, None],
)

def key_column_post():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据新增成功",
    "data": None
   }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    column_name = flask.request.json['name']
    column_id = flask.request.json['columnId']
    depository_id = flask.request.json['depositoryId']
    # 判断仓库是否存在
    try:
        mysql_depository = model_mysql_depository.query.filter(
            model_mysql_depository.id == depository_id
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_depository is None:
            return route.error_msgs[201]['msg_no_depository']
    # 判断是否存在父级目录
    if column_id==0:
        pass
    else:
        try:
            mysql_column_info = model_mysql_case.query.filter(
                model_mysql_case.id == column_id,
                model_mysql_case.depositoryId == depository_id,
                model_mysql_case.status == 1,
                model_mysql_case.type == 1
            ).first()
            api_logger.debug("账户基础信息读取成功")
        except Exception as e:
            api_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_column_info is None:
                return route.error_msgs[201]['msg_no_catalogue']



    # 判断目录是否已存在
    try:
        mysql_column_info = model_mysql_case.query.filter(
            model_mysql_case.title == column_name,
            model_mysql_case.depositoryId==depository_id,
            model_mysql_case.columnId==column_id,
            model_mysql_case.type==1
        ).first()
        api_logger.debug("账户基础信息读取成功")
    except Exception as e:
        api_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_column_info is None:
            new_column_info = model_mysql_case(
                title=column_name,
                depositoryId=depository_id,
                userId=request_user_id,
                columnId=column_id,
                level=0,
                type=1,
                status=1
            )
            mysqlpool.session.add(new_column_info)
            mysqlpool.session.commit()
        elif mysql_column_info.status == -1:

            mysql_column_info.status = 1
            mysqlpool.session.commit()
        else:
            return route.error_msgs[201]['msg_exit_catalogue']


    # 最后返回内容
    return response_json