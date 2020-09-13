# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool
from handler.log import api_logger

from model.mysql import model_mysql_project
from model.mysql import model_mysql_projectMember
"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断测试项目是否存在
            删除项目信息(变更项目状态)
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_delete_parameter(
    ['id', int, 1, None],
    ['userId', int, 1, None]
)
def key_projectmember_delete():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据删除成功",
    "data": None
    }


    # 取出入参
    project_user_id = flask.request.headers['UserId']
    project_id = flask.request.args['id']
    projectmember_id = flask.request.args['userId']


    # 判断项目是否存在
    try:
        mysql_project_info = model_mysql_project.query.filter(
            model_mysql_project.id == project_id,model_mysql_project.userId==project_user_id
        ).first()
        api_logger.debug("账户基础信息读取成功")
    except Exception as e:
        api_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_project_info is None:
            return route.error_msgs[201]['msg_no_project']

    #判断项目成员是否合法且存在

    try:
        mysql_projectmember_info = model_mysql_projectMember.query.filter(
            model_mysql_projectMember.userId == projectmember_id,model_mysql_projectMember.projectId==project_id
        ).first()
        api_logger.debug("账户基础信息读取成功")
    except Exception as e:
        api_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_projectmember_info is None:
            return route.error_msgs[201]['msg_no_projectmember']

    if mysql_projectmember_info.type==1:
        return route.error_msgs[201]['msg_user_cannot_operate']
    else:
        mysql_projectmember_info.status=-1
        mysqlpool.session.commit()



    # 最后返回内容
    return response_json
