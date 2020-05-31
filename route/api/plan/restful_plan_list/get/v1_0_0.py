# -*- coding: utf-8 -*-

import flask
import json
import route

from sqlalchemy import func, and_

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_tablesnap
from model.mysql import model_mysql_userinfo
from model.redis import model_redis_userinfo

"""
    查看个人目录下所有的测试计划-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断操作者和被查询的账户是否是同一人，如果是，返回所有测试计划；如果否，只返回开放浏览的测试计划
            构建测试计划清单数据，并最终返回
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['userId', int, 1, None],
    ['sortType', int, 1, None],
    ['numPerPage', int, 1, None],
    ['pageNumber', int, 1, None],
    ['keyword', str, 0, 100]
)
def plan_list_get():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {
            "total": 0,
            "plan_list": []
        }
    }

    operate_user_id = None
    # 取出请求头内必要信息
    operator_mail_address = flask.request.headers['Mail']
    # 取出入参
    user_id = int(flask.request.args['userId'])
    sort_type = int(flask.request.args['sortType'])
    number_per_page = int(flask.request.args['numPerPage'])
    page_number = int(flask.request.args['pageNumber'])
    key_word = flask.request.args['keyword']

    # 查询缓存中账户信息，并取出账户id
    redis_userinfo = model_redis_userinfo.query(user_email=operator_mail_address)
    # 如果缓存中没查到，则查询mysql
    if redis_userinfo is None:
        try:
            mysql_userinfo = model_mysql_userinfo.query.filter(
                model_mysql_userinfo.userEmail == operator_mail_address
            ).first()
            api_logger.debug("账户基础信息读取成功")
        except Exception as e:
            api_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_userinfo is None:
                return route.error_msgs[201]['msg_no_user']
            else:
                operate_user_id = mysql_userinfo.userId
    else:
        # 格式化缓存基础信息内容
        try:
            redis_userinfo_json = json.loads(redis_userinfo.decode("utf8"))
            api_logger.debug("缓存账户数据json格式化成功")
        except Exception as e:
            api_logger.error("缓存账户数据json格式化失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_json_format_fail']
        else:
            operate_user_id = redis_userinfo_json['userId']

    """
        预备测试计划开放级别
        级别说明：
        1 全开放 开放包括浏览、复制等一系列功能给其他登录系统的操作者
        2 仅阅读 仅开放浏览功能给其他登录系统的操作者
        3 私有 不开放浏览等功能，仅支持本人操作
    """
    open_level = 4 if operate_user_id == user_id else 3
    # 查询mysql中测试计划数据
    # 查询测试计划总数
    try:
        mysql_planlist_number_query = mysqlpool.session.query(
            func.count(model_mysql_planinfo.planId),
        )
        if key_word == '':
            mysql_planlist_number = mysql_planlist_number_query.filter(
                model_mysql_planinfo.ownerId == user_id,
                model_mysql_planinfo.planOpenLevel < open_level
            ).first()
        else:
            mysql_planlist_number = mysql_planlist_number_query.filter(
                model_mysql_planinfo.ownerId == user_id,
                model_mysql_planinfo.planOpenLevel < open_level,
                model_mysql_planinfo.planTitle.like('%' + key_word + '%')
            ).first()
    except Exception as e:
        api_logger.error("测试计划数量读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        response_json['data']['total'] = mysql_planlist_number[0]

    # 查询测试计划
    try:
        sort_type_condition = None
        if sort_type == 1:
            sort_type_condition = model_mysql_planinfo.planAddTime.desc()
        elif sort_type == 2:
            sort_type_condition = model_mysql_planinfo.planAddTime.asc()
        elif sort_type == 3:
            sort_type_condition = model_mysql_tablesnap.snapAddTime.desc()
        else:
            sort_type_condition = model_mysql_tablesnap.snapAddTime.asc()
        mysql_plan_list_query = mysqlpool.session.query(
            model_mysql_planinfo.planId.label('planId'),
            model_mysql_planinfo.planTitle.label('planTitle'),
            model_mysql_planinfo.planDescription.label('planDescription'),
            model_mysql_planinfo.planOpenLevel.label('planOpenLevel'),
            model_mysql_planinfo.planType.label('planType'),
            model_mysql_planinfo.planAddTime.label('planAddTime'),
            model_mysql_planinfo.planUpdateTime.label('planUpdateTime'),
            model_mysql_userinfo.userId.label('userId'),
            model_mysql_userinfo.userEmail.label('userEmail'),
            model_mysql_userinfo.userNickName.label('userNickName'),
            model_mysql_tablesnap.snapAddTime.label('snapAddTime')
        ).outerjoin(
            model_mysql_userinfo,
            model_mysql_userinfo.userId == model_mysql_planinfo.ownerId
        ).outerjoin(
            model_mysql_tablesnap,
            and_(
                model_mysql_planinfo.planId == model_mysql_tablesnap.planId,
                model_mysql_tablesnap.status == 1
            )
        )
        if key_word == '':
            mysql_plan_list = mysql_plan_list_query.filter(
                model_mysql_userinfo.userId == user_id,
                model_mysql_planinfo.status == 1,
                model_mysql_planinfo.planOpenLevel < open_level
            ).order_by(
                sort_type_condition
            ).limit(
                number_per_page
            ).offset(
                (page_number - 1) * number_per_page
            ).all()
        else:
            mysql_plan_list = mysql_plan_list_query.filter(
                model_mysql_userinfo.userId == user_id,
                model_mysql_planinfo.status == 1,
                model_mysql_planinfo.planOpenLevel < open_level,
                model_mysql_planinfo.planTitle.like('%' + key_word + '%')
            ).order_by(
                sort_type_condition
            ).limit(
                number_per_page
            ).offset(
                (page_number - 1) * number_per_page
            ).all()
    except Exception as e:
        api_logger.error("测试计划数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        for data in mysql_plan_list:
            # noinspection PyTypeChecker
            response_json['data']['plan_list'].append({
                'id': data.planId,
                'title': data.planTitle,
                'description': data.planDescription,
                'type': data.planType,
                'openLevel': data.planOpenLevel,
                'authorId': data.userId,
                'authorNickName': data.userNickName,
                'authorMail': data.userEmail,
                'addTime': str(data.planAddTime),
                'updateTime': str(data.planUpdateTime),
                'lastEditTime': str(data.snapAddTime) if data.snapAddTime else None
            })

    # 最后返回内容
    return response_json