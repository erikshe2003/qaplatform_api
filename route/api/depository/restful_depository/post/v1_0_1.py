# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_depository
from model.mysql import model_mysql_userinfo
from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_case
"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断测试项目是否存在
            新增项目
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['name', str, 1, 50],
    ['description', str, 0, 250],
)
def key_depository_post():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据新增成功",
        "data": {}
    }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    depository_name = flask.request.json['name']
    depository_description = flask.request.json['description']

    # 判断user_id获取角色信息
    try:
        mysql_userinfo = model_mysql_userinfo.query.filter(
            model_mysql_userinfo.userId == request_user_id
        ).first()
        api_logger.debug("账户基础信息读取成功")
    except Exception as e:
        api_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_userinfo is None:
            return route.error_msgs[201]['msg_no_user']

    # 查询名称是否存在
    try:
        mysql_depository = model_mysql_depository.query.filter(
            model_mysql_depository.name == depository_name
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_depository is not None:
            return route.error_msgs[201]['msg_exit_depository']

    # 新增仓库基础信息
    new_depository_info = model_mysql_depository(
        userId=request_user_id,
        name=depository_name,
        description=depository_description,
    )
    try:
        mysqlpool.session.add(new_depository_info)
        mysqlpool.session.commit()
    except Exception as e:
        api_logger.error("仓库基础信息新增失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    # 最后返回内容
    return response_json
