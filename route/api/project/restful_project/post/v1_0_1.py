# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_project
from model.mysql import model_mysql_projectMember
from model.mysql import model_mysql_depository

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
    ['depositoryId', int, 1, None]

)
def key_project_post():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据新增成功",
        "data": None
    }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    project_name = flask.request.json['name']
    project_description = flask.request.json['description']
    project_coverOssPath = flask.request.json['coverOssPath']
    project_depositoryId = flask.request.json['depositoryId']

    # 查仓库是否存在
    try:
        mysql_depository = model_mysql_depository.query.filter(
            model_mysql_depository.id == project_depositoryId
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_depository is None:
            return route.error_msgs[201]['msg_no_depository']
        else:
            pass

    # 查询项目名称是否存在
    try:
        mysql_project = model_mysql_project.query.filter(
            model_mysql_project.name == project_name,
            model_mysql_project.depositoryId == project_depositoryId,
            model_mysql_project.status!=-1
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_project is None:
            pass
        else:
            return route.error_msgs[201]['msg_exit_project']

    """
        插入项目数据

    """
    new_project_info = model_mysql_project(

        userId=request_user_id,
        name=project_name,
        description=project_description,
        coverOssPath=project_coverOssPath,
        depositoryId=project_depositoryId,
        status=1

    )
    mysqlpool.session.add(new_project_info)
    mysqlpool.session.commit()

    # 获取项目id
    try:
        mysql_depository_info = model_mysql_project.query.filter(
            model_mysql_project.name == project_name,
            model_mysql_project.depositoryId == project_depositoryId,
            model_mysql_project.status != -1
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_depository_info is None:
            return route.error_msgs[201]['msg_no_project']
        else:
            pass
    """
        插入项目管理员

    """
    new_projectMember_info = model_mysql_projectMember(

        projectId=mysql_depository_info.id,
        userId=request_user_id,
        type=1,
        status=1

    )
    mysqlpool.session.add(new_projectMember_info)
    mysqlpool.session.commit()
    # 缺少copy仓库用例逻辑***************************最新设计不需要拷贝

    # 最后返回内容
    return response_json
