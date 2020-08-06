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
            变更用例状态
            添加评审记录
            返回操作结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(

    ['ids', str, None, None],
    ['reviewerId', int, 1, None]
)

def key_caseReview_post():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "提交成功",
    "data": None
   }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    case_ids = flask.request.json['ids']
    reviewer_id= flask.request.json['reviewerId']
    id_list=case_ids.split(',')

    if len(case_ids)==0:
        return route.error_msgs[301]['msg_value_type_error']
    # 判断用例是否存在
    for case_id in id_list:

        try:
            mysql_case_info = model_mysql_case.query.filter(
                model_mysql_case.id == case_id,
                model_mysql_case.type == 2,
                model_mysql_case.status == 1,
                model_mysql_case.veri==0
            ).first()
        except Exception as e:
            api_logger.error("数据读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_case_info is None:
                pass

            else:
                mysql_case_info.veri=1
                new_case_review=model_mysql_projectReviewRecord(
                    caseId=case_id,
                    initiatorId=request_user_id,
                    reviewerId=reviewer_id,
                    result=0
                )
                mysqlpool.session.add(new_case_review)
                mysqlpool.session.commit()
    return response_json