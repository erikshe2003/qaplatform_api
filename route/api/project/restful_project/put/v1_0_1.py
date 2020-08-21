# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_project

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断测试项目是否存在
            新增项目
            添加项目管理员
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(

    ['name', str, 1, 50],
    ['description', str, 0, 250],
    ['coverOssPath', str, 0, 250],
    ['id', int, 1, None]

)

def key_project_put():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据修改成功",
    "data": None
   }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    project_name = flask.request.json['name']
    project_description = flask.request.json['description']
    project_coverOssPath = flask.request.json['coverOssPath']
    project_id = flask.request.json['id']

     # 查询项目名称是否存在
    try:
        mysql_project = model_mysql_project.query.filter(
            model_mysql_project.id==project_id,
            model_mysql_project.status==1
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_project is None:

            return route.error_msgs[201]['msg_no_project']

        else:
            mysql_project.name=project_name
            mysql_project.description=project_description
            mysql_project.coverOssPath=project_coverOssPath
            mysqlpool.session.commit()



    # 最后返回内容
    return response_json