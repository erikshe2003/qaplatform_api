# -*- coding: utf-8 -*-

import flask
import json
import route
import datetime

from sqlalchemy import func, and_

from handler.log import api_logger
from handler.pool import mysqlpool

from route.api.plan import api_plan

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_plancase
from model.mysql import model_mysql_planstep
from model.mysql import model_mysql_planplugin
from model.mysql import model_mysql_planversion
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
            检查caseList/stepList/pluginList内关键参数是否存在以及对应数据格式是否符合要求
            检查测试计划是否存在
            检查发起人是否为测试计划所有者
            检查版本id是否为该计划对应的工作台临时版本id
            更新plan基础信息
            更新plan下case信息
            更新plan信息
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

    # 检查plan中必输项
    plan_data = flask.request.json['plan']
    if 'id' not in plan_data or type(plan_data['id']) is not int or plan_data['id'] < 1:
        return route.error_msgs['msg_data_error']

    # 检查caseList/stepList/pluginList内关键参数是否存在以及对应数据格式是否符合要求
    table_data = flask.request.json['table']
    # if 'id' not in table_data or type(table_data['id']) is not int or table_data['id'] < 1:
    #     return route.error_msgs['msg_data_error']
    if 'title' not in table_data or type(table_data['title']) is not str or len(table_data['title']) > 50:
        return route.error_msgs['msg_data_error']
    if 'description' not in table_data or type(table_data['description']) is not str or len(table_data['description']) > 200:
        return route.error_msgs['msg_data_error']
    if 'caseList' not in table_data or type(table_data['caseList']) is not list:
        return route.error_msgs['msg_data_error']
    c = 0
    s = 0
    p = 0
    for cl in table_data['caseList']:
        if 'id' in cl:
            if type(cl['id']) is not int or cl['id'] < 1:
                return route.error_msgs['msg_data_error']
        if 'title' not in cl or type(cl['title']) is not str or len(cl['title']) > 50:
            return route.error_msgs['msg_data_error']
        if 'description' not in cl or type(cl['description']) is not str or len(cl['description']) > 200:
            return route.error_msgs['msg_data_error']
        if 'status' not in cl or type(cl['status']) is not int or cl['status'] not in [0, 1]:
            return route.error_msgs['msg_data_error']
        if 'sequence' not in cl or type(cl['sequence']) is not int or cl['sequence'] != c:
            return route.error_msgs['msg_data_error']
        if 'stepList' not in cl or type(cl['stepList']) is not list:
            return route.error_msgs['msg_data_error']
        for sl in cl['stepList']:
            if 'id' in sl:
                if type(sl['id']) is not int or sl['id'] < 1:
                    return route.error_msgs['msg_data_error']
            if 'status' not in sl or type(sl['status']) is not int or sl['status'] not in [0, 1]:
                return route.error_msgs['msg_data_error']
            if 'sequence' not in sl or type(sl['sequence']) is not int or sl['sequence'] != s:
                return route.error_msgs['msg_data_error']
            if 'pluginList' not in sl or type(sl['pluginList']) is not list:
                return route.error_msgs['msg_data_error']
            if len(sl['pluginList']) < 1:
                return route.error_msgs['msg_data_error']
            for pl in sl['pluginList']:
                if 'id' in pl:
                    if type(pl['id']) is not int or pl['id'] < 1:
                        return route.error_msgs['msg_data_error']
                if 'title' not in pl or type(pl['title']) is not str or len(pl['title']) > 50:
                    return route.error_msgs['msg_data_error']
                if 'description' not in pl or type(pl['description']) is not str or len(pl['description']) > 200:
                    return route.error_msgs['msg_data_error']
                if 'status' not in pl or type(pl['status']) is not int or pl['status'] not in [0, 1]:
                    return route.error_msgs['msg_data_error']
                if 'originalId' not in pl or type(pl['originalId']) is not int or pl['originalId'] < 1:
                    return route.error_msgs['msg_data_error']
                if 'sequence' not in pl or type(pl['sequence']) is not int or pl['sequence'] != p:
                    return route.error_msgs['msg_data_error']
                if 'value' not in pl or type(pl['value']) is not str:
                    return route.error_msgs['msg_data_error']
                p += 1
            p = 0
            s += 1
        s = 0
        c += 1

    # 查询测试计划基础信息，并取出所属者账户id
    plan_id = flask.request.json['plan']['id']
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

    # 查询测试计划下为临时版本的版本信息
    # version_id = flask.request.json['table']['id']
    version_title = flask.request.json['table']['title']
    version_description = flask.request.json['table']['description']
    try:
        mysql_temp_version = model_mysql_planversion.query.filter(
            and_(
                model_mysql_planversion.planId == plan_id,
                model_mysql_planversion.isTemporary == 1
            )
        ).first()
        api_logger.debug("Plan=" + str(plan_id) + "的mysql_temp_version数据读取成功")
    except Exception as e:
        api_logger.error("Plan=" + str(plan_id) + "的mysql_temp_version数据读取失败，失败原因：" + repr(e))
        return route.error_msgs['msg_db_error']
    else:
        """
            1.按照传入内容新增/修改工作台临时版本的信息
        """
        if mysql_temp_version is None:
            mysql_temp_version = model_mysql_planversion(
                    planId=plan_id,
                    versionTitle=version_title,
                    versionDescription=version_description,
                    isTemporary=1,
                    msg=""
                )
            mysqlpool.session.add(mysql_temp_version)
        else:
            mysql_temp_version.versionTitle = version_title
            mysql_temp_version.versionDescription = version_description
        mysqlpool.session.commit()

    """
        遍历mysql_caselist其中数据：
        1.delete掉历史数据
        2.逐条add
    """
    version_id = mysql_temp_version.versionId
    # 1.
    try:
        mysql_caselist = model_mysql_plancase.query.filter(
            model_mysql_plancase.versionId == version_id
        ).all()
        api_logger.debug("VersionId=" + str(version_id) + "的mysql_caselist数据读取成功")
    except Exception as e:
        api_logger.error("VersionId=" + str(version_id) + "的mysql_caselist数据读取失败，失败原因：" + repr(e))
        return route.error_msgs['msg_db_error']
    else:
        for mysql_case in mysql_caselist:
            # 查询测试用例下相关测试步骤
            try:
                mysql_steplist = model_mysql_planstep.query.filter(
                    model_mysql_planstep.caseId == mysql_case.caseId
                ).all()
                api_logger.debug("caseId=" + str(mysql_case.caseId) + "的mysql_steplist数据读取成功")
            except Exception as e:
                api_logger.error("caseId=" + str(mysql_case.caseId) + "的mysql_steplist数据读取失败，失败原因：" + repr(e))
                return route.error_msgs['msg_db_error']
            else:
                for mysql_step in mysql_steplist:
                    # 查询测试步骤下相关测试插件
                    model_mysql_planplugin.query.filter(
                        model_mysql_planplugin.stepId == mysql_step.stepId
                    ).delete()
                    try:
                        mysqlpool.session.commit()
                        api_logger.debug("stepId=" + str(mysql_step.stepId) + "的插件数据清空成功")
                    except Exception as e:
                        api_logger.error("stepId=" + str(mysql_step.stepId) + "的插件数据清空失败，失败原因：" + repr(e))
                        return route.error_msgs['msg_db_error']
                    model_mysql_planstep.query.filter(
                        model_mysql_planstep.stepId == mysql_step.stepId
                    ).delete()
                    try:
                        mysqlpool.session.commit()
                        api_logger.debug("stepId=" + str(mysql_step.stepId) + "的数据删除成功")
                    except Exception as e:
                        api_logger.error("stepId=" + str(mysql_step.stepId) + "的数据删除失败，失败原因：" + repr(e))
                        return route.error_msgs['msg_db_error']
            model_mysql_plancase.query.filter(
                model_mysql_plancase.caseId == mysql_case.caseId
            ).delete()
            try:
                mysqlpool.session.commit()
                api_logger.debug("caseId=" + str(mysql_case.caseId) + "的数据删除成功")
            except Exception as e:
                api_logger.error("caseId=" + str(mysql_case.caseId) + "的数据删除失败，失败原因：" + repr(e))
                return route.error_msgs['msg_db_error']

    # 2.
    caselist = flask.request.json['table']['caseList']
    for case in caselist:
        new_mysql_case = model_mysql_plancase(
            versionId=version_id,
            sequence=case['sequence'],
            status=case['status'],
            caseTitle=case['title'],
            caseDescription=case['description']
        )
        mysqlpool.session.add(new_mysql_case)
        mysqlpool.session.commit()
        # 新增测试用例后新增下属的测试步骤
        for step in case['stepList']:
            new_mysql_step = model_mysql_planstep(
                caseId=new_mysql_case.caseId,
                sequence=step['sequence'],
                status=step['status']
            )
            mysqlpool.session.add(new_mysql_step)
            mysqlpool.session.commit()
            # 新增测试步骤后新增下属的测试插件
            for plugin in step['pluginList']:
                new_mysql_plugin = model_mysql_planplugin(
                    stepId=new_mysql_step.stepId,
                    originalId=plugin['originalId'],
                    sequence=plugin['sequence'],
                    status=plugin['status'],
                    title=plugin['title'],
                    description=plugin['description'],
                    value=plugin['value']
                )
                mysqlpool.session.add(new_mysql_plugin)
                mysqlpool.session.commit()

    # 最后返回内容
    return json.dumps(response_json)
