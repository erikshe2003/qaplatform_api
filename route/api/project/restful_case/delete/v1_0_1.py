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
@route.check_delete_parameter(

    ['id', int, 1, None]
)

def key_case_delete():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据删除成功",
    "data":  None

   }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    case_id = flask.request.args['id']

    # 查用例是否存在,构造基础信息
    try:
        mysql_case_info = model_mysql_case.query.filter(
            model_mysql_case.id == case_id,model_mysql_case.type==2
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_case_info is None:
            return route.error_msgs[201]['msg_no_case']
        else:
            indexchang(mysql_case_info.index, mysql_case_info.columnId)
            mysql_case_info.status=-1
            mysql_case_info.updateUserId=request_user_id
            mysql_case_info.index = 0
            mysqlpool.session.commit()


    return response_json
#改变后续的排序
def indexchang(index,columnId):
    # 将后面的用例index+1
    try:
        back_case = model_mysql_case.query.filter(
            model_mysql_case.index >= index, model_mysql_case.type == 2, model_mysql_case.status == 1,
            model_mysql_case.columnId == columnId
        ).all()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if back_case is None:
            pass
        else:
            for mqti in back_case:
                mqti.index -= 1
                mysqlpool.session.commit()