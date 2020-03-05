# -*- coding: utf-8 -*-

import flask
import json
import route

from sqlalchemy import func, and_

from handler.log import api_logger
from handler.pool import mysqlpool

from route.api.plan import api_plan

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_plantype
from model.mysql import model_mysql_userinfo
from model.redis import model_redis_userinfo

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


@api_plan.route('/addPersonalPlan.json', methods=["post"])
@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['mailAddress', str, 1, 100],
    ['planType', int, 1, 1],
    ['planTitle', str, 1, 50],
    ['planDescription', str, 0, 200],
    ['openLevel', int, 1, 3]
)
def add_personal_plan():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {}
    }

    user_id = None
    # 取出必传入参
    mail_address = flask.request.json['mailAddress']
    plan_type = flask.request.json['planType']
    plan_title = flask.request.json['planTitle']
    open_level = flask.request.json['openLevel']
    plan_description = flask.request.json['planDescription']

    # 查询缓存中账户信息，并取出账户id
    redis_userinfo = model_redis_userinfo.query(user_email=mail_address)
    # 如果缓存中没查到，则查询mysql
    if redis_userinfo is None:
        try:
            mysql_userinfo = model_mysql_userinfo.query.filter(
                model_mysql_userinfo.userEmail == mail_address
            ).first()
            api_logger.debug(mail_address + "的账户基础信息读取成功")
        except Exception as e:
            api_logger.error(mail_address + "的账户基础信息读取失败，失败原因：" + repr(e))
            return route.error_msgs['msg_db_error']
        else:
            if mysql_userinfo is None:
                return route.error_msgs['msg_no_user']
            else:
                user_id = mysql_userinfo.userId
    else:
        # 格式化缓存基础信息内容
        try:
            redis_userinfo_json = json.loads(redis_userinfo.decode("utf8"))
            api_logger.debug(mail_address + "的缓存账户数据json格式化成功")
        except Exception as e:
            api_logger.error(mail_address + "的缓存账户数据json格式化失败，失败原因：" + repr(e))
            return route.error_msgs['msg_json_format_fail']
        else:
            user_id = redis_userinfo_json['userId']

    # 查询测试计划类型是否存在
    try:
        mysql_plantype = model_mysql_plantype.query.filter(
            model_mysql_plantype.typeId == plan_type
        ).first()
    except Exception as e:
        api_logger.error(mail_address + "的测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs['msg_db_error']
    else:
        if mysql_plantype is None:
            return route.error_msgs['msg_no_plan_type']

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
    return json.dumps(response_json)
