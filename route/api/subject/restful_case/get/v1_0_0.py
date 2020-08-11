# -*- coding: utf-8 -*-

import flask

import route


from handler.log import api_logger

from model.mysql import model_mysql_subjectcase
from model.mysql import model_mysql_subjectcasestep
from model.mysql import model_mysql_subjectcaseprecondition
"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断是否存在
            返回基础信息
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['subjectId', int, 1, None],
    ['catalogueId', int, 1, None],
    ['caseId', int, 1, None]
)
def key_case_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data": {
        "caseId": None,
        "caseName": None,
        "type": 1,
        "status": 1,
        "precondition": None,
        "steps": [],
        "createTime": None,
        "updateTime": None
    }
}


    # 取出入参

    case_id = flask.request.args['caseId']
    subject_id = flask.request.args['subjectId']
    catalogue_id = flask.request.args['catalogueId']

    # 查询case基础信息
    try:
        mysql_case_info = model_mysql_subjectcase.query.filter(
            model_mysql_subjectcase.caseId == case_id
        ).first()
    except Exception as e:
        api_logger.error("model_mysql_subjectinfo数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    finally:
        if mysql_case_info is None:
            return route.error_msgs[201]['msg_no_case']
        else:
            response_json['data']['caseId'] = mysql_case_info.caseId
            response_json['data']['caseName'] = mysql_case_info.caseName
            response_json['data']['type'] = mysql_case_info.caseType
            response_json['data']['status'] = mysql_case_info.caseStatus
            response_json['data']['createTime'] = mysql_case_info.caseCreateTime
            response_json['data']['updateTime'] = mysql_case_info.caseUpdateTime

    # 查询caseprecondition基础信息
    try:
        mysql_casesteps = model_mysql_subjectcaseprecondition.query.filter(
                model_mysql_subjectcaseprecondition.caseId == case_id
            ).first()
    except Exception as e:
            api_logger.error("model_mysql_subjectinfo数据读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
    finally:
            if mysql_casesteps is None:
                pass
            else:
                for step in mysql_casesteps:
                    response_json["data"]["steps"].append({
                        "stepId": step.stepId,
                        "stepName": step.stepName,
                        "expetation": step.expetation,
                        "createTime": step.stepCreateTime,
                        "updateTime": step.setpUpdateTime,
                    })



    # 最后返回内容
    return response_json
