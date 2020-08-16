# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_casePrecondition
from model.mysql import model_mysql_case
from model.mysql import model_mysql_caseFile
from model.mysql import model_mysql_caseStep
from model.mysql import model_mysql_caseEditLog

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断目录是否存在
            判断title等必输项是否为空
            添加用例
            添加前置条件
            添加附件
            添加用例步骤
            调整用例排序
            返回操作结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(

    ['columnId', int, 1, None],
    ['title', str, 1, None],
    ['frontCaseId', int, None, None],
    ['level', int, 1, None],
    ['casePrecondition', str, None, None],
    ['caseStep', list, 0, None],
    ['files', list, 0, None],

)
def key_case_post():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据新增成功",
        "data": None
    }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    case_columnId = flask.request.json['columnId']
    case_title = flask.request.json['title']
    case_level = flask.request.json['level']
    front_case = flask.request.json['frontCaseId']
    case_precondition = flask.request.json['casePrecondition']
    case_step = flask.request.json['caseStep']
    files = flask.request.json['files']

    # 查目录是否存在
    try:
        mysql_column = model_mysql_case.query.filter(
            model_mysql_case.id == case_columnId, model_mysql_case.type == 1, model_mysql_case.status == 1
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_column is None:
            return route.error_msgs[201]['msg_no_catalogue']
        else:
            pass

    # 判断必输项title、front_case和level必传
    if len(case_title) == 0:
        return route.error_msgs[201]['msg_data_error']
    elif case_level is None:
        return route.error_msgs[201]['msg_data_error']
    elif front_case is None:
        return route.error_msgs[201]['msg_data_error']

    # 查同名用例是否存在
    try:
        mysql_case = model_mysql_case.query.filter(
            model_mysql_case.title == case_title, model_mysql_case.type == 2, model_mysql_case.status == 1,
            model_mysql_case.columnId == case_columnId
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_case is None:
            pass
        else:
            return route.error_msgs[201]['msg_case_exit']

    # 插入用例主数据
    if front_case == 0:
        index = 1
        indexchang(index, case_columnId)
        new_case_info = model_mysql_case(

            title=case_title,
            columnId=case_columnId,
            projectId=mysql_column.projectId,
            index=index,
            level=case_level,
            type=2,
            status=1,
            veri=0,
            arch=0,
            userId=request_user_id,
            depositoryId=mysql_column.depositoryId,
            originalCaseId=0

        )
        mysqlpool.session.add(new_case_info)
        mysqlpool.session.commit()
    else:
        try:
            mysql_front = model_mysql_case.query.filter(
                model_mysql_case.id == front_case, model_mysql_case.type == 2, model_mysql_case.status == 1
            ).first()
        except Exception as e:
            api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_front is None:
                return route.error_msgs[201]['msg_no_case']
            else:
                index = mysql_front.index + 1
                indexchang(index, case_columnId)
                new_case_info = model_mysql_case(

                    title=case_title,
                    columnId=case_columnId,
                    projectId=mysql_column.projectId,
                    index=index,
                    level=case_level,
                    type=2,
                    status=1,
                    veri=0,
                    arch=0,
                    userId=request_user_id,
                    depositoryId=mysql_column.depositoryId,
                    originalCaseId=0

                )
                mysqlpool.session.add(new_case_info)
                mysqlpool.session.commit()

    # 获取用例id
    try:
        mysql_case_info = model_mysql_case.query.filter(
            model_mysql_case.title == case_title, model_mysql_case.type == 2, model_mysql_case.status == 1,
            model_mysql_case.index == index
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_case_info is None:
            return route.error_msgs[201]['msg_no_case']

    precondition(mysql_case_info.id, case_precondition)
    osspath(mysql_case_info.id, request_user_id, files)
    casestep(mysql_case_info.id, case_step, request_user_id)

    # 添加日志
    case_logs = model_mysql_caseEditLog(
        caseId=mysql_case_info.id,
        type=1
    )
    mysqlpool.session.add(case_logs)
    mysqlpool.session.commit()

    # 最后返回内容
    return response_json


# 改变后续的排序
def indexchang(index, columnid):
    # 将后面的用例index+1
    try:
        back_case = model_mysql_case.query.filter(
            model_mysql_case.index >= index, model_mysql_case.type == 2, model_mysql_case.status == 1,
            model_mysql_case.columnId == columnid
        ).all()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if back_case is None:
            pass
        else:
            for mqti in back_case:
                mqti.index += 1
                mysqlpool.session.commit()


def precondition(caseid, case_precondition):
    # 插入前置条件
    if len(case_precondition) == 0:
        pass
    else:
        new_caseprecondition_info = model_mysql_casePrecondition(
            content=case_precondition,
            caseId=caseid
        )
        mysqlpool.session.add(new_caseprecondition_info)
        mysqlpool.session.commit()


def osspath(caseid, userid, files):
    # 插入附件oss地址
    if len(files) == 0:
        pass
    else:
        for x in files:
            new_casefile_info = model_mysql_caseFile(
                ossPath=x['ossPath'],
                caseId=caseid,
                status=1,
                userId=userid,
                fileAlias=x['fileAlias']

            )

            mysqlpool.session.add(new_casefile_info)

            mysqlpool.session.commit()


def casestep(caseid, case_step, userid):
    # 插入测试步骤
    # 这里一定要注意传入数组的参数中千万不能有空格，否则会死都查不出为啥会错，python的json方法无法解析，postman居然可以识别。

    if len(case_step) == 0:
        pass
    else:
        try:
            for x in case_step:
                new_casestep_info = model_mysql_caseStep(
                    index=x['index'],
                    caseId=caseid,
                    content=x['content'],
                    expectation=x['expectation'],
                    status=1,
                    userId=userid
                )
                mysqlpool.session.add(new_casestep_info)
                mysqlpool.session.commit()
        except Exception as e:
            api_logger.error("测试数据读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']