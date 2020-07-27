# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_casePrecondition
from model.mysql import model_mysql_case
from model.mysql import model_mysql_caseFile
from model.mysql import model_mysql_caseStep
from model.mysql import model_mysql_depository
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

    ['depositoryId', int, 1, None],
    ['columnId', int, 1, None],
    ['keyWord', str, None, None]

)

def key_cases_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data": []
   }

    cases_id=[]
    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    depository_id = flask.request.args['depositoryId']
    column_id = flask.request.args['columnId']
    key_word = flask.request.args['keyWord']


    #判断仓库是否存在
    try:
        mysql_depository_info = model_mysql_depository.query.filter(
            model_mysql_depository.id == depository_id
        ).first()
    except Exception as e:
        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_depository_info is None:
            return route.error_msgs[201]['msg_no_depository']
    #判断目录是否存在
    try:
        mysql_column_info = model_mysql_case.query.filter(
            model_mysql_case.columnId == column_id,
            model_mysql_case.status==1,
            model_mysql_case.type==1,
            model_mysql_case.depositoryId == depository_id
        ).first()
    except Exception as e:
        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_column_info is None:
            return route.error_msgs[201]['msg_no_catalogue']

    # 判断keyword是否存在


    if len(key_word)==0:
        # 查询满足条件的测试用例编号

        try:
            mysql_cases_id = model_mysql_case.query.filter(
                model_mysql_case.columnId == column_id,
                model_mysql_case.depositoryId == depository_id,
                model_mysql_case.status == 1,
                model_mysql_case.type == 2,
                model_mysql_case.veri ==3,
                model_mysql_case.arch ==2
            ).order_by(model_mysql_case.index).all()
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if len(mysql_cases_id) ==0:
                return route.error_msgs[201]['msg_no_case']
            else:
                for x in mysql_cases_id:

                    cases_id.append(x.id)

    else:
        # 查询满足条件的测试用例编号
        try:
            mysql_cases_id = model_mysql_case.query.filter(
                model_mysql_case.columnId == column_id,
                model_mysql_case.depositoryId == depository_id,
                model_mysql_case.status == 1,
                model_mysql_case.type == 2,
                model_mysql_case.veri ==3,
                model_mysql_case.arch ==2,
                model_mysql_case.title.like('%'+key_word+'%')
            ).order_by(model_mysql_case.index).all()
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if len(mysql_cases_id) == 0:
                return route.error_msgs[201]['msg_no_case']
            else:
                for x in mysql_cases_id:

                    cases_id.append(x.id)

    count=0
    for case_id in cases_id:
        # 查用例是否存在,构造基础信息
        try:
            mysql_case_info = model_mysql_case.query.filter(
                model_mysql_case.id == case_id, model_mysql_case.type == 2, model_mysql_case.status == 1
            ).first()
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_case_info is None:
                return route.error_msgs[201]['msg_no_case']
            else:
                response_json['data'].append({
                    'id':mysql_case_info.id,
                    'columnId': mysql_case_info.columnId,
                    'title':mysql_case_info.title,
                    'level':mysql_case_info.level,
                    'index':mysql_case_info.index,
                    'casePrecondition':None,
                    'ossPath':None,
                    'caseStep':[]

                })


        # 查询是否存在前置条件
        try:
            mysql_casePrecondition_info = model_mysql_casePrecondition.query.filter(
                model_mysql_casePrecondition.caseId == case_id
            ).first()
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_casePrecondition_info is None:
                pass
            else:
                response_json['data'][count]['casePrecondition']= mysql_casePrecondition_info.content



        # 查询是否存在附件
        try:
            mysql_caseFile_info = model_mysql_caseFile.query.filter(
                model_mysql_caseFile.caseId == case_id, model_mysql_caseFile.status == 1
            ).first()
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_caseFile_info is None:
                pass
            else:
                response_json['data'][count]['ossPath'] = mysql_casePrecondition_info.content

        # 查询是否存在测试步骤
        try:
            mysql_caseStep_info = model_mysql_caseStep.query.filter(
                model_mysql_caseStep.caseId == case_id,model_mysql_caseStep.status==1
            ).order_by(model_mysql_caseStep.index).all()
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_caseStep_info is None:
                pass
            else:
                for mqti in mysql_caseStep_info:

                    response_json['data'][count]['caseStep'].append({
                        "id": mqti.id,
                        "content": mqti.content,
                        "expectation": mqti.expectation,
                        "index": mqti.index
                    })
        count+=1


    return response_json