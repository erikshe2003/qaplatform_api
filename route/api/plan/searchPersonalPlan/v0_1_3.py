# -*- coding: utf-8 -*-

import flask
import json
import route

from sqlalchemy import func, and_

from handler.log import api_logger
from handler.pool import mysqlpool

from route.api.plan import api_plan

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_planversion
from model.mysql import model_mysql_userinfo
from model.redis import model_redis_userinfo

"""
    按照计划名称搜索符合要求的个人目录下的测试计划-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断操作者和被查询的账户是否是同一人，如果是，返回所有测试计划；如果否，只返回开放浏览的测试计划
            构建测试计划清单数据，并最终返回
"""


@api_plan.route('/searchPersonalPlan.json', methods=["post"])
@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['mailAddress', str, 1, 100],
    ['keyWords', str, 1, 50],
    ['numPerPage', int, 1, None],
    ['pageNumber', int, 1, None]
)
def search_personal_plan():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {
            "total": 0,
            "plan_list": []
        }
    }

    user_id = None
    # 取出请求头内必要信息
    operator_mail_address = flask.request.headers['Mail']
    # 取出入参
    mail_address = flask.request.json['mailAddress']
    mail_key_words = flask.request.json['keyWords']
    number_per_page = flask.request.json['numPerPage']
    page_number = flask.request.json['pageNumber']

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

    """
        预备测试计划开放级别
        级别说明：
        1 全开放 开放包括浏览、复制等一系列功能给其他登录系统的操作者
        2 仅阅读 仅开放浏览功能给其他登录系统的操作者
        3 私有 不开放浏览等功能，仅支持本人操作
    """
    open_level = 4 if operator_mail_address == mail_address else 3
    # 查询mysql中测试计划数据
    # 查询测试计划总数
    try:
        mysql_planlist_number = mysqlpool.session.query(
            func.count(model_mysql_planinfo.planId),
        ).filter(
            and_(
                model_mysql_planinfo.ownerId == user_id,
                model_mysql_planinfo.planOpenLevel < open_level,
                model_mysql_planinfo.planTitle.like('%' + mail_key_words + '%')
            )
        ).first()
    except Exception as e:
        api_logger.error(mail_address + "的测试计划数量读取失败，失败原因：" + repr(e))
        return route.error_msgs['msg_db_error']
    else:
        response_json['data']['total'] = mysql_planlist_number[0]

    # 查询测试计划
    # 编写子查询
    try:
        mysql_planversion_list = mysqlpool.session.query(
            model_mysql_planversion.planId.label('planId'),
            func.max(model_mysql_planversion.versionAddTime).label('versionAddTime')
        ).group_by(
            model_mysql_planversion.planId
        ).subquery()
    except Exception as e:
        api_logger.error(mail_address + "的测试计划子查询操作失败，失败原因：" + repr(e))
        return route.error_msgs['msg_db_error']
    else:
        try:
            mysql_plan_list = mysqlpool.session.query(
                model_mysql_planinfo.planId.label('planId'),
                model_mysql_planinfo.planTitle.label('planTitle'),
                model_mysql_planinfo.planDescription.label('planDescription'),
                model_mysql_planinfo.planOpenLevel.label('planOpenLevel'),
                model_mysql_planinfo.planType.label('planType'),
                model_mysql_planinfo.planAddTime.label('planAddTime'),
                model_mysql_planinfo.planUpdateTime.label('planUpdateTime'),
                model_mysql_planversion.versionId.label('versionId'),
                model_mysql_planversion.versionTitle.label('versionTitle'),
                model_mysql_planversion.versionDescription.label('versionDescription'),
                mysql_planversion_list.c.versionAddTime.label('versionAddTime'),
                model_mysql_planversion.versionUpdateTime.label('versionUpdateTime'),
                model_mysql_userinfo.userId.label('userId'),
                model_mysql_userinfo.userEmail.label('userEmail'),
                model_mysql_userinfo.userNickName.label('userNickName')
            ).outerjoin(
                mysql_planversion_list,
                mysql_planversion_list.c.planId == model_mysql_planinfo.planId
            ).outerjoin(
                model_mysql_planversion,
                and_(
                    model_mysql_planversion.planId == mysql_planversion_list.c.planId,
                    model_mysql_planversion.versionAddTime == mysql_planversion_list.c.versionAddTime
                )
            ).outerjoin(
                model_mysql_userinfo,
                model_mysql_userinfo.userId == model_mysql_planinfo.ownerId
            ).filter(
                and_(
                    model_mysql_userinfo.userId == user_id,
                    model_mysql_planinfo.planOpenLevel < open_level,
                    model_mysql_planinfo.planTitle.like('%' + mail_key_words + '%')
                )
            ).order_by(
                model_mysql_planinfo.planAddTime.desc()
            ).limit(
                number_per_page
            ).offset(
                (page_number - 1) * number_per_page
            ).all()
        except Exception as e:
            api_logger.error(mail_address + "的测试计划数据读取失败，失败原因：" + repr(e))
            return route.error_msgs['msg_db_error']
        else:
            for data in mysql_plan_list:
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
                    'newest_version': {
                        'id': data.versionId,
                        'title': data.versionTitle,
                        'description': data.versionDescription,
                        'addTime': str(data.versionAddTime),
                        'updateTime': str(data.versionUpdateTime)
                    }
                })

    # 最后返回内容
    return json.dumps(response_json)
