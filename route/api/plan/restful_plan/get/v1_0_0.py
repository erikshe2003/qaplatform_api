# -*- coding: utf-8 -*-

import flask
import json
import route

from sqlalchemy import func

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_tablesnap
from model.mysql import model_mysql_userinfo
from model.redis import model_redis_userinfo

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断测试计划是否存在
            返回测试计划基础信息
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['planId', int, 1, None]
)
def plan_get():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {
            "id": 0,
            "title": "",
            "mail": "",
            "description": "",
            "type": 0,
            "openLevel": 0,
            "addTime": None,
            "forkCount": 0,
            "snap": {
                "count": 0,
                "firstAddTime": None,
                "lastAddTime": None
            },
            "contributorCount": 0
        }
    }

    request_user_id = None
    plan_user_id = None
    # 取出入参
    request_head_mail = flask.request.headers['Mail']
    response_json['data']['mail'] = request_head_mail
    plan_id = flask.request.args['planId']

    # 查询测试计划基础信息，并取出所属者账户id
    try:
        mysql_plan_info = model_mysql_planinfo.query.filter(
            model_mysql_planinfo.planId == plan_id
        ).first()
    except Exception as e:
        api_logger.error("model_mysql_planinfo数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_plan_info is None:
            return route.error_msgs[201]['msg_no_plan']
        else:
            plan_user_id = mysql_plan_info.ownerId
            response_json['data']['id'] = mysql_plan_info.planId
            response_json['data']['title'] = mysql_plan_info.planTitle
            response_json['data']['description'] = mysql_plan_info.planDescription
            response_json['data']['type'] = mysql_plan_info.planType
            response_json['data']['addTime'] = str(mysql_plan_info.planAddTime)
            response_json['data']['openLevel'] = mysql_plan_info.planOpenLevel

    # 查询缓存中账户信息，并取出账户id
    redis_userinfo = model_redis_userinfo.query(user_email=request_head_mail)
    # 如果缓存中没查到，则查询mysql
    if redis_userinfo is None:
        try:
            mysql_userinfo = model_mysql_userinfo.query.filter(
                model_mysql_userinfo.userEmail == request_head_mail
            ).first()
            api_logger.debug("Mail=" + request_head_mail + "的model_redis_userinfo信息读取成功")
        except Exception as e:
            api_logger.error("Mail=" + request_head_mail + "的model_redis_userinfo信息读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_userinfo is None:
                return route.error_msgs[201]['msg_no_user']
            else:
                request_user_id = mysql_userinfo.userId
    else:
        # 格式化缓存基础信息内容
        try:
            redis_userinfo_json = json.loads(redis_userinfo.decode("utf8"))
            api_logger.debug("Mail=" + request_head_mail + "的缓存账户数据json格式化成功")
        except Exception as e:
            api_logger.error("Mail=" + request_head_mail + "的缓存账户数据json格式化失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_json_format_fail']
        else:
            request_user_id = redis_userinfo_json['userId']

    # 根据测试计划开放级别以及操作者id/计划拥有者id判断返回内容
    if request_user_id == plan_user_id:
        pass
    else:
        if mysql_plan_info.planOpenLevel in (1, 2):
            pass
        else:
            return route.error_msgs[201]['msg_plan_notopen']

    # 查询测试计划被复制次数
    try:
        mysql_fork_count = mysqlpool.session.query(
            func.count(model_mysql_planinfo.planId).label("forkCount")
        ).filter(
            model_mysql_planinfo.forkFrom == plan_id
        ).first()
    except Exception as e:
        api_logger.error("PlanId=" + plan_id + "的model_mysql_planinfo数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        response_json['data']['forkCount'] = mysql_fork_count.forkCount

    # 查询测试计划下快照数据
    # 条目数
    try:
        mysql_snap_count = mysqlpool.session.query(
            func.count(model_mysql_tablesnap.id).label('count')
        ).filter(
            model_mysql_tablesnap.planId == plan_id
        ).first()
    except Exception as e:
        api_logger.error("model_mysql_tablesnap数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        response_json['data']['snap']['count'] = mysql_snap_count.count
    # 第一次保存时间
    try:
        mysql_snap_first_snap = model_mysql_tablesnap.query.filter(
            model_mysql_tablesnap.planId == plan_id
        ).order_by(
            model_mysql_tablesnap.id.asc()
        ).limit(1).first()
    except Exception as e:
        api_logger.error("model_mysql_tablesnap数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_snap_first_snap is not None:
            response_json['data']['snap']['firstAddTime'] = str(mysql_snap_first_snap.snapAddTime)
    # 最后一次保存时间
    try:
        mysql_snap_last_snap = model_mysql_tablesnap.query.filter(
            model_mysql_tablesnap.planId == plan_id
        ).order_by(
            model_mysql_tablesnap.id.desc()
        ).limit(1).first()
    except Exception as e:
        api_logger.error("model_mysql_tablesnap数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_snap_last_snap is not None:
            response_json['data']['snap']['lastAddTime'] = str(mysql_snap_last_snap.snapAddTime)

    # 最后返回内容
    return response_json
