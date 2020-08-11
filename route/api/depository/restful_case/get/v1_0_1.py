# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_casePrecondition
from model.mysql import model_mysql_case
from model.mysql import model_mysql_caseFile
from model.mysql import model_mysql_caseStep
"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断用例是否存在
            返回操作结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(

    ['id', int, 1, None]
)

def key_case_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data": {
        "id":0,
        "columnId": None,
        "title": None,
        "index": None,
        "level": None,
        "casePrecondition": None,
        "caseStep": [],
        "ossPath": []
    }
   }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    case_id = flask.request.args['id']

    # 查用例是否存在,构造基础信息
    try:
        mysql_case_info = model_mysql_case.query.filter(
            model_mysql_case.id == case_id,model_mysql_case.type==2,model_mysql_case.status==1
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_case_info is None:
            return route.error_msgs[201]['msg_no_case']
        else:
            response_json['data']['id'] =mysql_case_info.id
            response_json['data']['columnId']=mysql_case_info.columnId
            response_json['data']['title'] = mysql_case_info.title
            response_json['data']['level'] = mysql_case_info.level
            response_json['data']['index'] = mysql_case_info.index

    #查询是否存在前置条件
    try:
        mysql_casePrecondition_info = model_mysql_casePrecondition.query.filter(
            model_mysql_casePrecondition.caseId == case_id
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_casePrecondition_info is None:
            pass
        else:
            response_json['data']['casePrecondition'] =mysql_casePrecondition_info.content

    #查询是否存在附件
    try:
        mysql_caseFile_info = model_mysql_caseFile.query.filter(
            model_mysql_caseFile.caseId == case_id,model_mysql_caseFile.status==1
        ).all()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_caseFile_info is None:
            pass
        else:
            for x in mysql_caseFile_info:
                response_json['data']['ossPath'].append({
                "id":x.id,
                "ossPath":x.ossPath,
                "fileAlias":x.fileAlias
                }
                )

    #查询是否存在测试步骤
    try:
        mysql_caseStep_info = model_mysql_caseStep.query.filter(
            model_mysql_caseStep.caseId == case_id,model_mysql_caseStep.status==1
        ).all()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_caseStep_info is None:
            pass
        else:
            for mqti in mysql_caseStep_info:

                response_json['data']['caseStep'].append({
                    "id":mqti.id,
                    "content":mqti.content,
                    "expectation":mqti.expectation,
                    "index":mqti.index
                })

    return response_json