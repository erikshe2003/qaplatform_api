# -*- coding: utf-8 -*-

import flask
import json
import route

from sqlalchemy import and_

from handler.log import api_logger

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_tablesnap
from model.mysql import model_mysql_userinfo
from model.redis import model_redis_userinfo

"""
    查看某个个人测试计划的工作台的最新快照内容-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            需判断操作者是否为计划所有者
            查询快照的istatus为1的，返回其下所有内容
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['planId', int, 0, None]
)
def plan_worktable_snap_get():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {
            "plan": {
                "id": 0,
                "title": "",
                "type": 0,
                "openLevel": 0
            },
            "snap": {
                "id": 0,
                "data": ''
            }
        }
    }

    request_user_id = None
    plan_user_id = None
    case_list = []
    # 取出入参
    request_head_mail = flask.request.headers['Mail']
    plan_id = int(flask.request.args['planId'])

    # 查询测试计划基础信息，并取出所属者账户id
    try:
        mysql_plan_info = model_mysql_planinfo.query.filter(
            model_mysql_planinfo.planId == plan_id
        ).first()
    except Exception as e:
        api_logger.error("PlanId=" + str(plan_id) + "的model_mysql_planinfo数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_plan_info is None:
            return route.error_msgs[201]['msg_no_plan']
        else:
            plan_user_id = mysql_plan_info.ownerId
            response_json['data']['plan']['id'] = mysql_plan_info.planId
            response_json['data']['plan']['title'] = mysql_plan_info.planTitle
            response_json['data']['plan']['type'] = mysql_plan_info.planType
            response_json['data']['plan']['openLevel'] = mysql_plan_info.planOpenLevel

    # 查询缓存中账户信息，并取出账户id
    redis_userinfo = model_redis_userinfo.query(user_email=request_head_mail)
    # 如果缓存中没查到，则查询mysql
    if redis_userinfo is None:
        try:
            mysql_userinfo = model_mysql_userinfo.query.filter(
                model_mysql_userinfo.userEmail == request_head_mail
            ).first()
            api_logger.debug("Mail=" + request_head_mail + "的model_mysql_userinfo数据读取成功")
        except Exception as e:
            api_logger.error("Mail=" + request_head_mail + "的model_mysql_userinfo数据读取失败，失败原因：" + repr(e))
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

    # 如果操作者和计划拥有者不是同一人，则报错
    if plan_user_id != request_user_id:
        return route.error_msgs[201]['msg_plan_notopen']

    # 查询快照
    try:
        mysql_snap_data = model_mysql_tablesnap.query.filter(
            and_(
                model_mysql_tablesnap.planId == plan_id,
                model_mysql_tablesnap.status == 1
            )
        ).first()
        api_logger.debug("Plan=" + str(plan_id) + "的mysql_temp_version数据读取成功")
    except Exception as e:
        api_logger.error("Plan=" + str(plan_id) + "的mysql_temp_version数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        # 如果无临时版本，则返回空数据
        if mysql_snap_data is None:
            pass
        else:
            response_json['data']['snap']['id'] = mysql_snap_data.id
            response_json['data']['snap']['data'] = mysql_snap_data.table
            response_json['data']['snap']['addTime'] = str(mysql_snap_data.snapAddTime)

    # 最后返回内容
    return response_json
