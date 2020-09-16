# -*- coding: utf-8 -*-

import flask
import route

from handler.pool import mysqlpool
from handler.log import api_logger

from sqlalchemy.sql import func

from model.mysql import model_mysql_casePrecondition
from model.mysql import model_mysql_case
from model.mysql import model_mysql_caseFile
from model.mysql import model_mysql_caseStep
from model.mysql import model_mysql_caseEditLog


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['columnId', int, 1, None],
    ['projectId', int, 1, None],
    ['title', str, 1, 200],
    ['level', int, 1, 3],
    ['precondition', str, 0, 500],
    ['steps', list, 0, None],
    ['files', list, 0, None],
)
def key_case_post():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据新增成功",
        "data": {}
    }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    request_column_id = flask.request.json['columnId']
    request_project_id = flask.request.json['projectId']
    request_title = flask.request.json['title']
    request_level = flask.request.json['level']
    request_precondition = flask.request.json['precondition']
    request_steps = flask.request.json['steps']
    request_files = flask.request.json['files']

    # 查目录是否存在
    try:
        mysql_column = model_mysql_case.query.filter(
            model_mysql_case.id == request_column_id,
            model_mysql_case.type == 1,
            model_mysql_case.status == 1
        ).first()
    except Exception as e:
        api_logger.error("项目数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_column is None:
            return route.error_msgs[201]['msg_no_catalogue']

    # 插入用例主数据
    # 获取目录下用例的最大index
    try:
        mysql_cases_max_index = mysqlpool.session.query(
            func.max(model_mysql_case.index)
        ).filter(
            model_mysql_case.columnId == mysql_column.id,
            model_mysql_case.depositoryId == mysql_column.depositoryId,
            model_mysql_case.status != -1,
            model_mysql_case.type == 2
        ).first()[0]
        api_logger.debug("用例信息读取成功")
    except Exception as e:
        api_logger.error("用例信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    new_case_info = model_mysql_case(
        title=request_title,
        depositoryId=mysql_column.depositoryId,
        projectId=request_project_id,
        columnId=request_column_id,
        index=mysql_cases_max_index + 1 if mysql_cases_max_index is not None else 1,
        columnLevel=0,
        level=request_level,
        type=2,
        status=1,
        userId=request_user_id,
        veri=0,
        arch=0,
        originalCaseId=0
    )
    mysqlpool.session.add(new_case_info)
    try:
        mysqlpool.session.commit()
        api_logger.error("用例基础信息新增成功")
    except Exception as e:
        api_logger.error("用例基础信息新增失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    # 一次性检查前置条件+步骤+附件
    # 前置条件
    # 此项可为空字符串
    mysqlpool.session.add(model_mysql_casePrecondition(
        content=request_precondition,
        caseId=new_case_info.id
    ))
    # 步骤
    for rs in request_steps:
        if 'content' not in rs or 'expectation' not in rs or 'index' not in rs:
            return route.error_msgs[302]['msg_request_params_incomplete']
        elif type(rs['content']) is not str or type(rs['expectation']) is not str or type(rs['index']) is not int:
            return route.error_msgs[302]['msg_request_params_illegal']
        else:
            mysqlpool.session.add(model_mysql_caseStep(
                caseId=new_case_info.id,
                index=rs['index'],
                content=rs['content'],
                expectation=rs['expectation'],
                status=1,
                userId=request_user_id
            ))
    # 附件
    for rf in request_files:
        if 'ossPath' not in rf or 'fileAlias' not in rf:
            return route.error_msgs[302]['msg_request_params_incomplete']
        elif type(rf['ossPath']) is not str or type(rf['fileAlias']) is not str:
            return route.error_msgs[302]['msg_request_params_illegal']
        else:
            mysqlpool.session.add(model_mysql_caseFile(
                ossPath=rf['ossPath'],
                caseId=new_case_info.id,
                status=1,
                userId=request_user_id,
                fileAlias=rf['fileAlias']
            ))

    # 添加日志
    mysqlpool.session.add(model_mysql_caseEditLog(
        caseId=new_case_info.id,
        type=1
    ))

    # 入库
    try:
        mysqlpool.session.commit()
        api_logger.error("用例前置条件信息新增成功")
    except Exception as e:
        api_logger.error("用例前置条件信息新增失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    
    response_json['data'] = {
        'id': new_case_info.id,
        'title': new_case_info.title,
        'depositoryId': new_case_info.depositoryId,
        'projectId': new_case_info.projectId,
        'columnId': new_case_info.columnId,
        'index': new_case_info.index,
        'columnLevel': new_case_info.columnLevel,
        'level': new_case_info.level,
        'type': new_case_info.type,
        'status': new_case_info.status,
        'userId': new_case_info.userId,
        'createTime': str(new_case_info.createTime),
        'updateUserId': new_case_info.updateUserId,
        'updateTime': str(new_case_info.updateTime),
        'veri': new_case_info.veri,
        'arch': new_case_info.arch,
        'originalCaseId': new_case_info.originalCaseId
    }

    # 最后返回内容
    return response_json
