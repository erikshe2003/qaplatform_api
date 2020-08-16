# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_caseEditLog
from model.mysql import model_mysql_casePrecondition
from model.mysql import model_mysql_case
from model.mysql import model_mysql_caseFile
from model.mysql import model_mysql_caseStep
from model.mysql import model_mysql_project

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

    ['id', int, 1, None],
    ['projectId', int, 1, None]
)
def key_case_delete():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据删除成功",
        "data": None

    }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    case_id = flask.request.args['id']
    project_id = flask.request.args['projectId']

    # 获取用例的全部信息
    try:
        mysql_case_info = model_mysql_case.query.filter(
            model_mysql_case.id == case_id, model_mysql_case.type == 2
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_case_info is None:
            return route.error_msgs[201]['msg_no_case']
        else:

            # 判断是否是仓库的用例
            if int(mysql_case_info.projectId) == int(project_id):

                indexchang(mysql_case_info.index, mysql_case_info.columnId)
                mysql_case_info.status = -1
                mysql_case_info.updateUserId = request_user_id
                mysql_case_info.index = 0
                mysqlpool.session.commit()

                # 添加日志

                case_logs = model_mysql_caseEditLog(
                    caseId=mysql_case_info.id,
                    type=7

                )
                mysqlpool.session.add(case_logs)
                mysqlpool.session.commit()
            else:

                # 获取原用例信息
                case_title = mysql_case_info.title
                case_depositoryId = mysql_case_info.depositoryId
                case_projectId = project_id
                case_columnId = mysql_case_info.columnId
                case_index = mysql_case_info.index
                case_level = mysql_case_info.level
                case_type = 2
                case_userId = request_user_id
                case_status = 3
                case_veri = 1
                case_arch = 0
                case_step = []
                oss_path = []

                # 获取原用例的前置条件
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
                        case_precondition = None
                        pass
                    else:
                        case_precondition = mysql_casePrecondition_info.content
                # # 查询是否存在附件
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
                        for mqti in mysql_caseFile_info:
                            oss_path.append({
                                "id": mqti.id,
                                "ossPath": mqti.ossPath,
                                "fileAlias": mqti.fileAlias
                            })
                # 查询是否存在测试步骤
                try:
                    mysql_caseStep_info = model_mysql_caseStep.query.filter(
                        model_mysql_caseStep.caseId == case_id, model_mysql_caseStep.status == 1
                    ).order_by(model_mysql_caseStep.index).all()
                except Exception as e:
                    api_logger.error("读取失败，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']
                else:
                    if mysql_caseStep_info is None:
                        pass
                    else:
                        for mqti in mysql_caseStep_info:
                            case_step.append({
                                "id": mqti.id,
                                "content": mqti.content,
                                "expectation": mqti.expectation,
                                "index": mqti.index
                            })

                # 备份新的用例
                new_case_info = model_mysql_case(

                    title=case_title,
                    columnId=case_columnId,
                    projectId=case_projectId,
                    index=case_index,
                    level=case_level,
                    type=case_type,
                    status=case_status,
                    veri=case_veri,
                    arch=case_arch,
                    userId=case_userId,
                    depositoryId=case_depositoryId,
                    originalCaseId=case_id,
                    updateUserId=case_userId

                )
                mysqlpool.session.add(new_case_info)
                mysqlpool.session.commit()

                # 获得主用例编号
                try:
                    mysql_id = model_mysql_case.query.filter(
                        model_mysql_case.projectId == case_projectId, model_mysql_case.type == 2,
                        model_mysql_case.status == 3,
                        model_mysql_case.columnId == case_columnId, model_mysql_case.originalCaseId == case_id
                    ).first()
                except Exception as e:
                    api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']
                else:
                    if mysql_id is None:
                        return route.error_msgs[201]['msg_no_case']

                # 前置条件
                if case_precondition is None:
                    pass
                else:
                    new_caseprecondition_info = model_mysql_casePrecondition(
                        content=case_precondition,
                        caseId=mysql_id.id
                    )
                    mysqlpool.session.add(new_caseprecondition_info)
                # 附件
                if len(oss_path) == 0:
                    pass
                else:
                    for x in oss_path:
                        new_casefile_info = model_mysql_caseFile(
                            ossPath=x['ossPath'],
                            caseId=mysql_id.id,
                            status=1,
                            userId=case_userId,
                            fileAlias=x['fileAlias']
                        )

                        mysqlpool.session.add(new_casefile_info)
                # 步骤
                if len(case_step) == 0:
                    pass
                else:
                    for x in case_step:
                        new_casestep_info = model_mysql_caseStep(
                            index=x['index'],
                            caseId=mysql_id.id,
                            content=x['content'],
                            expectation=x['expectation'],
                            status=1,
                            userId=case_userId,
                            updateUserId=case_userId
                        )
                        mysqlpool.session.add(new_casestep_info)
                mysqlpool.session.commit()
                # 添加日志
                case_logs = model_mysql_caseEditLog(
                    caseId=mysql_id.id,
                    type=1
                )
                mysqlpool.session.add(case_logs)
                mysqlpool.session.commit()

    return response_json


# 改变后续的排序
def indexchang(index, columnId):
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
