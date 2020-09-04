# -*- coding: utf-8 -*-

import flask
import route

from handler.pool import mysqlpool
from handler.log import api_logger

from model.mysql import model_mysql_project
from model.mysql import model_mysql_projectMember
from model.mysql import model_mysql_depository


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['title', str, 1, 50],
    ['description', str, 0, 200],
    ['coverOssPath', str, 0, 200],
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
    project_name = flask.request.json['title']
    project_description = flask.request.json['description']
    project_oss_path = flask.request.json['coverOssPath']
    project_depository_id = flask.request.json['depositoryId']

    # 查仓库是否存在
    try:
        mysql_depository = model_mysql_depository.query.filter(
            model_mysql_depository.id == project_depository_id
        ).first()
    except Exception as e:
        api_logger.error("仓库数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_depository is None:
            return route.error_msgs[201]['msg_no_depository']

    # 查询项目名称是否存在
    try:
        mysql_project = model_mysql_project.query.filter(
            model_mysql_project.name == project_name,
            model_mysql_project.depositoryId == project_depository_id,
            model_mysql_project.status != -1
        ).first()
    except Exception as e:
        api_logger.error("项目数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_project is not None:
            return route.error_msgs[201]['msg_exit_project']

    """
        插入项目数据
    """
    new_project_info = model_mysql_project(
        userId=request_user_id,
        name=project_name,
        description=project_description,
        coverOssPath=project_oss_path,
        depositoryId=project_depository_id,
        status=1
    )
    mysqlpool.session.add(new_project_info)

    try:
        mysqlpool.session.commit()
    except Exception as e:
        api_logger.error("项目数据新增失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    # 当前创建时直接指定创建人为项目管理员
    new_project_admin = model_mysql_projectMember(
        projectId=new_project_info.id,
        userId=request_user_id,
        type=1,
        status=1
    )
    mysqlpool.session.add(new_project_admin)

    try:
        mysqlpool.session.commit()
    except Exception as e:
        api_logger.error("项目成员数据新增失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    # 最后返回内容
    return response_json
