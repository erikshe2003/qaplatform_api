# -*- coding: utf-8 -*-

import flask

import route

from handler.log import api_logger

from model.mysql import model_mysql_projectArchivePendingCase
from model.mysql import model_mysql_casePrecondition
from model.mysql import model_mysql_caseFile
from model.mysql import model_mysql_caseStep
from model.mysql import model_mysql_case
from model.mysql import model_mysql_project

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断项目是否存在，并且是否在冲突中
            获取项目冲突列表
            将冲突中的三方用例输出
            返回操作结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['projectId', int, 1, None]
)
def key_caseConflict_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据获取成功",
        "data": []
    }

    # 取出必传入参

    project_id = flask.request.args['projectId']

    # 判断项目是否存在,并且发起了评审，并获取仓库id
    try:
        mysql_project_info = model_mysql_project.query.filter(
            model_mysql_project.id == project_id, model_mysql_project.status == 2
        ).first()
    except Exception as e:

        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_project_info is None:
            return response_json

    # 判断项目冲突是否存在
    try:
        mysql_conflict_info = model_mysql_projectArchivePendingCase.query.filter(
            model_mysql_projectArchivePendingCase.projectId == project_id,
            model_mysql_projectArchivePendingCase.status == 1
        ).all()
    except Exception as e:

        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_conflict_info is None:
            return response_json

    # 构造冲突结果返回信息
    for mq in mysql_conflict_info:
        originalCase = []
        projectIdCase = []
        otherCase = []
        originalCase.append(createcase(mq.originalCaseId))
        projectIdCase.append(createcase(mq.projectIdCaseId))
        otherCase.append(createcase(mq.otherCaseId))
        response_json["data"].append({
            "id": mq.id,
            "projectId": project_id,
            "projectName": mysql_project_info.name,
            "originalCase": originalCase,
            "projectIdCase": projectIdCase,
            "otherCase": otherCase,
            "status": mq.status

        })

    return response_json


def createcase(case_id):
    case_json = {
        "id": 0,
        "columnId": None,
        "title": None,
        "index": None,
        "level": None,
        "casePrecondition": None,
        "originalCaseId": None,
        "caseStep": [],
        "ossPath": [],
        "status": 0
    }

    # 查用例是否存在,构造基础信息
    try:
        mysql_case_info = model_mysql_case.query.filter(
            model_mysql_case.id == case_id, model_mysql_case.type == 2
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_case_info is None:
            return None
        else:
            case_json['id'] = mysql_case_info.id
            case_json['columnId'] = mysql_case_info.columnId
            case_json['title'] = mysql_case_info.title
            case_json['level'] = mysql_case_info.level
            case_json['index'] = mysql_case_info.index
            case_json['originalCaseId'] = mysql_case_info.originalCaseId
            case_json['status'] = mysql_case_info.status

    # 查询是否存在前置条件
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
            case_json['casePrecondition'] = mysql_casePrecondition_info.content

    # 查询是否存在附件
    try:
        mysql_caseFile_info = model_mysql_caseFile.query.filter(
            model_mysql_caseFile.caseId == case_id, model_mysql_caseFile.status == 1
        ).all()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_caseFile_info is None:
            pass
        else:
            for mqti in mysql_caseFile_info:
                case_json['ossPath'].append({
                    "id": mqti.id,
                    "ossPath": mqti.ossPath,
                    "fileAlias": mqti.fileAlias
                })

    # 查询是否存在测试步骤
    try:
        mysql_caseStep_info = model_mysql_caseStep.query.filter(
            model_mysql_caseStep.caseId == case_id, model_mysql_caseStep.status == 1
        ).all()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_caseStep_info is None:
            pass
        else:
            for mqti in mysql_caseStep_info:
                case_json['caseStep'].append({
                    "id": mqti.id,
                    "content": mqti.content,
                    "expectation": mqti.expectation,
                    "index": mqti.index
                })

    return case_json
