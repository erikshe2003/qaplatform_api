# -*- coding: utf-8 -*-

import flask
import route

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_plantype
from model.mysql import model_mysql_userinfo

"""
    新增个人测试计划-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            校验测试计划类型是否存在
            新增个人测试计划
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['userId', int, 1, None],
    ['planType', int, 1, 2],
    ['planTitle', str, 1, 50],
    ['planDescription', str, 0, 200],
    ['openLevel', int, 1, 3]
)
def plan_post():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {}
    }

    # 取出必传入参
    user_id = flask.request.json['userId']
    plan_type = flask.request.json['planType']
    plan_title = flask.request.json['planTitle']
    open_level = flask.request.json['openLevel']
    plan_description = flask.request.json['planDescription']

    # 判断user_id是否存在
    try:
        mysql_userinfo = model_mysql_userinfo.query.filter(
            model_mysql_userinfo.userId == user_id
        ).first()
        api_logger.debug("账户基础信息读取成功")
    except Exception as e:
        api_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_userinfo is None:
            return route.error_msgs[201]['msg_no_user']

    # 查询测试计划类型是否存在
    try:
        mysql_plantype = model_mysql_plantype.query.filter(
            model_mysql_plantype.typeId == plan_type
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_plantype is None:
            return route.error_msgs[201]['msg_no_plan_type']

    """
        插入测试计划数据
        关于测试计划所有者类型：
        0 个人
        1 团队
    """
    new_plan_info = model_mysql_planinfo(
        ownerId=user_id,
        planType=plan_type,
        planTitle=plan_title,
        planDescription=plan_description if plan_description else None,
        planOpenLevel=open_level,
        planOwnerType=0
    )
    mysqlpool.session.add(new_plan_info)
    mysqlpool.session.commit()

    # 最后返回内容
    return response_json
