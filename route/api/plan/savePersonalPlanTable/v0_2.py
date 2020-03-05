# -*- coding: utf-8 -*-

import flask
import json
import route
import datetime

from sqlalchemy import and_

from handler.log import api_logger
from handler.pool import mysqlpool

from route.api.plan import api_plan

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_tablesnap
from model.mysql import model_mysql_userinfo
from model.redis import model_redis_userinfo

"""
    保存个人测试计划的工作台内容-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            将内容保存至snap表
            返回保存状态
"""


@api_plan.route('/savePersonalPlanTable.json', methods=["post"])
@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['plan', dict, 0, None],
    ['table', dict, 0, None]
)
def save_personal_plan_table():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "工作台内容保存成功",
        "data": {}
    }

    # 取出入参
    request_head_mail = flask.request.headers['Mail']
    request_json_plan = flask.request.json['plan']
    request_json_table = flask.request.json['table']

    # 检查必输项以及格式
    if 'id' not in request_json_plan or type(request_json_plan['id']) is not int or request_json_plan['id'] < 1:
        return route.error_msgs['msg_data_error']
    if 'content' not in request_json_table or type(request_json_table['content']) is not str:
        return route.error_msgs['msg_data_error']

    # 检查table_content是否符合格式要求
    table_content = request_json_table['content']
    # json格式化
    try:
        table_content_json = json.loads(table_content)
    except Exception as e:
        api_logger.debug("table_content处理json格式化失败，失败原因：" + repr(e))
        return route.error_msgs['msg_data_error']
    else:
        # 递归其内容，检查必传项是否存在
        def recurse_for_key_check(obj):
            for o in obj:
                # 检查必传项：
                # 1.id
                if 'id' not in o:
                    return route.error_msgs['msg_data_error']
                # 2.originalId
                if 'originalId' not in o:
                    return route.error_msgs['msg_data_error']
                # 3.title
                if 'title' not in o:
                    return route.error_msgs['msg_data_error']
                # 4.desc
                if 'desc' not in o:
                    return route.error_msgs['msg_data_error']
                # 5.status
                if 'status' not in o:
                    return route.error_msgs['msg_data_error']
                # 6.children
                if 'children' not in o:
                    return route.error_msgs['msg_data_error']
                recurse_for_key_check(o['children'])
        recurse_for_key_check(table_content_json)

    # 查询测试计划基础信息，并取出所属者账户id
    plan_id = request_json_plan['id']
    try:
        mysql_plan_info = model_mysql_planinfo.query.filter(
            model_mysql_planinfo.planId == plan_id
        ).first()
    except Exception as e:
        api_logger.error("PlanId=" + str(plan_id) + "的model_mysql_planinfo数据读取失败，失败原因：" + repr(e))
        return route.error_msgs['msg_db_error']
    else:
        plan_user_id = mysql_plan_info.ownerId

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
            return route.error_msgs['msg_db_error']
        else:
            if mysql_userinfo is None:
                return route.error_msgs['msg_no_user']
            else:
                request_user_id = mysql_userinfo.userId
    else:
        # 格式化缓存基础信息内容
        try:
            redis_userinfo_json = json.loads(redis_userinfo.decode("utf8"))
            api_logger.debug("Mail=" + request_head_mail + "的缓存账户数据json格式化成功")
        except Exception as e:
            api_logger.error("Mail=" + request_head_mail + "的缓存账户数据json格式化失败，失败原因：" + repr(e))
            return route.error_msgs['msg_json_format_fail']
        else:
            request_user_id = redis_userinfo_json['userId']

    # 如果操作者和计划拥有者不是同一人，则报错
    if plan_user_id != request_user_id:
        return route.error_msgs['msg_plan_notopen']

    # 将status为1的snap全部置为失效
    try:
        mysql_snaps = model_mysql_tablesnap.query.filter(
            and_(
                model_mysql_tablesnap.planId == plan_id,
                model_mysql_tablesnap.status == 1
            )
        ).all()
    except Exception as e:
        api_logger.error("model_mysql_tablesnap数据读取失败，失败原因：" + repr(e))
        return route.error_msgs['msg_db_error']
    else:
        for s in mysql_snaps:
            s.status = 0
        try:
            mysqlpool.session.commit()
        except Exception as e:
            api_logger.error("mysql_snaps数据写入失败，失败原因：" + repr(e))
            return route.error_msgs['msg_db_error']

    # 新增status为1的snap，内容即为接口传参内容
    new_snap = model_mysql_tablesnap(
        status=1,
        planId=plan_id,
        snapAddTime=datetime.datetime.now(),
        table=table_content
    )
    try:
        mysqlpool.session.add(new_snap)
        mysqlpool.session.commit()
    except Exception as e:
        api_logger.error("new_snap数据写入失败，失败原因：" + repr(e))
        return route.error_msgs['msg_db_error']

    # 最后返回内容
    return json.dumps(response_json)
