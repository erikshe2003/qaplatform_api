# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_projectReviewRecord
from model.mysql import model_mysql_case

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断用例是否存在
            判断评审是否提交
            变更用例状态
            变更评审记录状态
            返回操作结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(

    ['caseId', int, None, None],
    ['result', int, None, None],
    ['projectId', int, None, None]

)

def key_caseReview_put():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "处理成功",
    "data": None
   }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    case_id = flask.request.json['caseId']
    result = flask.request.json['result']
    project_id = flask.request.json['projectId']
    #判断是否是一键评审,caseId需传0
    if case_id==0:
        #先将新增且通过评审后删除的用例，评审通过直接删除，不通过变更回veri状态
        try:
            mysql_cases_info1 = model_mysql_case.query.filter(
                model_mysql_case.type == 2,
                model_mysql_case.status ==3,
                model_mysql_case.veri == 1,
                model_mysql_case.originalCaseId == 0,
                model_mysql_case.projectId == project_id
            ).all()
        except Exception as e:
            api_logger.error("数据读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_cases_info1 is None:
                pass
            else:

                for xx in mysql_cases_info1:
                    if result ==3:
                        xx.status=-1
                        xx.veri=3
                    else:
                        xx.status = 1
                        xx.veri = 2
                    mysqlpool.session.commit()

        # 在处理其他用例


        try:
            mysql_cases_info = model_mysql_case.query.filter(
                model_mysql_case.type == 2,
                model_mysql_case.status.in_([1,3]),
                model_mysql_case.veri == 1,
                model_mysql_case.projectId == project_id
            ).all()
        except Exception as e:
            api_logger.error("数据读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_cases_info is None:
                return route.error_msgs[201]['msg_no_case']
            else:
                for mqcs in mysql_cases_info:

                    try:
                        mysql_reviewrecord_info = model_mysql_projectReviewRecord.query.filter(
                            model_mysql_projectReviewRecord.caseId == mqcs.id,
                            model_mysql_projectReviewRecord.reviewerId == request_user_id,
                            model_mysql_projectReviewRecord.result == 1
                        ).first()
                    except Exception as e:
                        api_logger.error("数据读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:

                        print(mysql_reviewrecord_info)
                        if mysql_reviewrecord_info is None:
                            return route.error_msgs[201]['msg_no_reviewrecode']
                        else:
                            mqcs.veri=result
                            mysql_reviewrecord_info.result=result
                            mysqlpool.session.commit()


    else:
        # 先将新增且通过评审后删除的用例，评审通过直接删除，不通过变更回veri状态
        try:
            mysql_cases_info2 = model_mysql_case.query.filter(
                model_mysql_case.id == case_id,
                model_mysql_case.type == 2,
                model_mysql_case.status == 3,
                model_mysql_case.veri == 1,
                model_mysql_case.originalCaseId == 0,
                model_mysql_case.projectId == project_id
            ).first()
        except Exception as e:
            api_logger.error("数据读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_cases_info2 is None:
                pass
            else:
                if result == 3:
                    mysql_cases_info2.status = -1
                    mysql_cases_info2.veri = 3
                else:
                    mysql_cases_info2.status = 1
                    mysql_cases_info2.veri = 2
                mysqlpool.session.commit()

        # 判断用例是否存在
        try:
            mysql_case_info = model_mysql_case.query.filter(
                model_mysql_case.id == case_id,
                model_mysql_case.type == 2,
                model_mysql_case.status.in_([1,3]),
                model_mysql_case.veri == 1,
                model_mysql_case.projectId == project_id
            ).first()
        except Exception as e:
            api_logger.error("数据读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_case_info is None:
                return route.error_msgs[201]['msg_no_case']
        # 判断是否存在评审记录
        try:
            mysql_reviewrecord_info = model_mysql_projectReviewRecord.query.filter(
                model_mysql_projectReviewRecord.caseId == case_id,
                model_mysql_projectReviewRecord.reviewerId == request_user_id,
                model_mysql_projectReviewRecord.result == 1
            ).first()
        except Exception as e:
            api_logger.error("数据读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_reviewrecord_info is None:
                return route.error_msgs[201]['msg_no_reviewrecode']

        mysql_case_info.veri = result
        mysql_reviewrecord_info.result = result
        mysqlpool.session.commit()

    return response_json