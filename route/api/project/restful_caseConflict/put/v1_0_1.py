# -*- coding: utf-8 -*-

import flask

import route

from handler.log import api_logger

from model.mysql import model_mysql_projectArchivePendingCase
from model.mysql import model_mysql_casePrecondition
from model.mysql import model_mysql_caseFile
from model.mysql import model_mysql_caseStep
from model.mysql import model_mysql_case
from model.mysql import model_mysql_project
from model.mysql import model_mysql_depositoryProjectFiledOrg

from handler.pool import mysqlpool

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参,ids支持传一个冲突id和多个，使用逗号隔开
            另外需要注意的是，批量处理勾选的冲突内容必须是同类的，即四种类型中之一
    ----操作
            判断冲突是否存在
            获取项目冲突列表
            获取冲突相关用例详情
            根据给出的处理接口状态进行冲突处理
            返回操作结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['ids', str, 1, None],
    ['result', int, -1, None],
    ['projectId', int, 1, None]
)
def key_caseConflict_put():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据处理成功",
        "data": []
    }

    # 取出必传入参

    confilict_ids = flask.request.json['ids']

    if len(confilict_ids) == 0:
        return route.error_msgs[301]['msg_request_params_illegal']

    conflict_id = confilict_ids.split(",")

    result = flask.request.json['result']
    project_id = flask.request.json['projectId']

    if len(conflict_id) != 1:
        # 一键冲突解决
        # 获取全部冲突数据
        # 判断项目冲突是否存在

        id_list = conflict_id

        # 批量解决冲突

        for x in id_list:
            case_info = []
            case_info.append(conflictDtail(x))
            try:
                # 根据处理选择解决冲突
                newcase_id = case_info[0]["detail"][0]["projectIdCase"][0]["id"]
                newcase_status = case_info[0]["detail"][0]["projectIdCase"][0]["status"]
                othercase_id = case_info[0]["detail"][0]["otherCase"][0]["id"]
                othercase_status = case_info[0]["detail"][0]["otherCase"][0]["status"]
                othercase_index = case_info[0]["detail"][0]["otherCase"][0]["index"]
                resolveconflict(x, result, newcase_id, newcase_status, othercase_id, othercase_status, othercase_index)
            except Exception as e:
                api_logger.error("读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']


    else:
        case_info = []
        # 单个冲突解决
        # 获取单个冲突详细信息

        case_info.append(conflictDtail(int(conflict_id[0])))

        try:
            # 根据处理选择解决冲突
            newcase_id = case_info[0]["detail"][0]["projectIdCase"][0]["id"]
            newcase_status = case_info[0]["detail"][0]["projectIdCase"][0]["status"]

            othercase_id = case_info[0]["detail"][0]["otherCase"][0]["id"]
            othercase_status = case_info[0]["detail"][0]["otherCase"][0]["status"]
            othercase_index = case_info[0]["detail"][0]["otherCase"][0]["index"]

            resolveconflict(int(conflict_id[0]), result, newcase_id, newcase_status, othercase_id, othercase_status,
                            othercase_index)
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']

    # 判断项目归档记录信息
    try:
        mysql_arc_record = model_mysql_depositoryProjectFiledOrg.query.filter(
            model_mysql_depositoryProjectFiledOrg.projectId == project_id,
            model_mysql_depositoryProjectFiledOrg.result == 1
        ).first()
    except Exception as e:

        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        # 项目没有归档冲突时
        if mysql_arc_record is None:
            return route.error_msgs[201]['msg_no_arcrecode']

    # 判断项目是否还有冲突项
    try:
        mysql_conflicts = model_mysql_projectArchivePendingCase.query.filter(
            model_mysql_projectArchivePendingCase.projectId == project_id,
            model_mysql_projectArchivePendingCase.status == 1
        ).first()
    except Exception as e:

        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        # 项目没有归档冲突时
        if mysql_conflicts is None:
            # 变更项目归档状态和归档记录状态
            try:
                mysql_project = model_mysql_project.query.filter(
                    model_mysql_project.id == project_id
                ).first()
            except Exception as e:

                api_logger.error("读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:
                if mysql_project is None:
                    pass
                else:

                    mysql_project.status = 3
                    mysql_arc_record.result = 2
                    mysqlpool.session.commit()

    return response_json


def resolveconflict(conflict_id, result, newcase_id, newcase_status, othercase_id, othercase_status, othercase_index):
    # 再次确认冲突是否存在
    try:
        mysql_conflict = model_mysql_projectArchivePendingCase.query.filter(
            model_mysql_projectArchivePendingCase.id == conflict_id,
            model_mysql_projectArchivePendingCase.status == 1
        ).first()
    except Exception as e:

        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_conflict is None:
            return route.error_msgs[201]['msg_no_conflict']

    # 场景1处理情况
    if newcase_status == 1 and othercase_status == 1:
        # 新增处理
        if result == 2:
            try:
                mysql_newcase_info = model_mysql_case.query.filter(
                    model_mysql_case.id == newcase_id, model_mysql_case.type == 2
                ).first()
            except Exception as e:
                api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:
                if mysql_newcase_info is None:
                    return route.error_msgs[201]['msg_no_case']
                else:
                    mysql_newcase_info.arch = 2
                    mysql_newcase_info.index = othercase_index + 1
                    mysql_conflict.status = 2
                    mysqlpool.session.commit()

        # 覆盖处理
        elif result == 3:
            # 处理新case
            try:
                mysql_newcase_info = model_mysql_case.query.filter(
                    model_mysql_case.id == newcase_id, model_mysql_case.type == 2
                ).first()
            except Exception as e:
                api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:
                if mysql_newcase_info is None:
                    return route.error_msgs[201]['msg_no_case']
                else:
                    mysql_newcase_info.arch = 2
                    mysql_conflict.status = 3
                    mysqlpool.session.commit()
            # 处理旧case
            try:
                mysql_othercase_info = model_mysql_case.query.filter(
                    model_mysql_case.id == othercase_id, model_mysql_case.type == 2
                ).first()
            except Exception as e:
                api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:
                if mysql_othercase_info is None:
                    return route.error_msgs[201]['msg_no_case']
                else:
                    mysql_othercase_info.status = 2
                    mysqlpool.session.commit()

        else:
            return route.error_msgs[201]['msg_no_conflict_code']
    # 场景2处理情况
    if newcase_status == 3 and othercase_status == 1:
        # 忽略处理

        if result == 0:
            try:
                mysql_newcase_info = model_mysql_case.query.filter(
                    model_mysql_case.id == newcase_id, model_mysql_case.type == 2
                ).first()
            except Exception as e:
                api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:
                if mysql_newcase_info is None:
                    return route.error_msgs[201]['msg_no_case']
                else:
                    mysql_newcase_info.arch = 2
                    mysql_conflict.status = 0
                    mysqlpool.session.commit()

        # 删除处理
        elif result == -1:
            # 处理新case
            try:
                mysql_newcase_info = model_mysql_case.query.filter(
                    model_mysql_case.id == newcase_id, model_mysql_case.type == 2
                ).first()
            except Exception as e:
                api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:
                if mysql_newcase_info is None:
                    return route.error_msgs[201]['msg_no_case']
                else:
                    mysql_newcase_info.arch = 2
                    mysql_newcase_info.status = -1
                    mysql_conflict.status = -1
                    mysqlpool.session.commit()
            # 处理旧case
            try:
                mysql_othercase_info = model_mysql_case.query.filter(
                    model_mysql_case.id == othercase_id, model_mysql_case.type == 2
                ).first()
            except Exception as e:
                api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:

                if mysql_othercase_info is None:
                    return route.error_msgs[201]['msg_no_case']
                else:
                    mysql_othercase_info.status = 3
                    mysqlpool.session.commit()

        else:
            return route.error_msgs[201]['msg_no_conflict_code']
    # 场景3处理情况
    if newcase_status == 1 and othercase_status == -1:
        # 忽略处理
        if result == 0:
            try:
                mysql_newcase_info = model_mysql_case.query.filter(
                    model_mysql_case.id == newcase_id, model_mysql_case.type == 2
                ).first()
            except Exception as e:
                api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:
                if mysql_newcase_info is None:
                    return route.error_msgs[201]['msg_no_case']
                else:
                    mysql_newcase_info.arch = 2
                    mysql_newcase_info.status = 2
                    mysql_conflict.status = 0
                    mysqlpool.session.commit()

        # 覆盖处理
        elif result == 3:
            # 处理新case
            try:
                mysql_newcase_info = model_mysql_case.query.filter(
                    model_mysql_case.id == newcase_id, model_mysql_case.type == 2
                ).first()
            except Exception as e:
                api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:
                if mysql_newcase_info is None:
                    return route.error_msgs[201]['msg_no_case']
                else:
                    mysql_newcase_info.arch = 2
                    mysql_conflict.status = 3
                    mysqlpool.session.commit()

        else:
            return route.error_msgs[201]['msg_no_conflict_code']
    # 场景4处理情况
    if newcase_status == 3 and othercase_status == -1:
        # 忽略处理
        if result == 0:
            try:
                mysql_newcase_info = model_mysql_case.query.filter(
                    model_mysql_case.id == newcase_id, model_mysql_case.type == 2
                ).first()
            except Exception as e:
                api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:
                if mysql_newcase_info is None:
                    return route.error_msgs[201]['msg_no_case']
                else:
                    mysql_newcase_info.arch = 2
                    mysql_newcase_info.status = -1
                    mysql_conflict.status = 0
                    mysqlpool.session.commit()

        else:
            return route.error_msgs[201]['msg_no_conflict_code']


def conflictDtail(conflict_id):
    response_conflict = {
        "detail": []
    }
    # 判断项目冲突是否存在
    try:
        mysql_conflict_info = model_mysql_projectArchivePendingCase.query.filter(
            model_mysql_projectArchivePendingCase.id == conflict_id,
            model_mysql_projectArchivePendingCase.status == 1
        ).first()
    except Exception as e:

        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_conflict_info is None:
            return response_conflict

    # 构造冲突结果返回信息
    originalCase = []
    projectIdCase = []
    otherCase = []
    originalCase.append(createcase(mysql_conflict_info.originalCaseId))
    projectIdCase.append(createcase(mysql_conflict_info.projectIdCaseId))
    otherCase.append(createcase(mysql_conflict_info.otherCaseId))
    response_conflict["detail"].append({
        "id": mysql_conflict_info.id,
        "projectId": mysql_conflict_info.projectId,
        "originalCase": originalCase,
        "projectIdCase": projectIdCase,
        "otherCase": otherCase,
        "status": mysql_conflict_info.status

    })

    return response_conflict


def createcase(case_id):
    case_json = {
        "id": 0,
        "columnId": None,
        "title": None,
        "index": None,
        "level": None,
        "casePrecondition": None,
        "originalCaseId": None,
        "status": None,
        "caseStep": [],
        "ossPath": []
    }

    # 查用例是否存在,构造基础信息
    try:
        mysql_case_info = model_mysql_case.query.filter(
            model_mysql_case.id == case_id, model_mysql_case.type == 2
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_case_info is None:
            return None
        else:
            case_json['id'] = mysql_case_info.id
            case_json['columnId'] = mysql_case_info.columnId
            case_json['title'] = mysql_case_info.title
            case_json['level'] = mysql_case_info.level
            case_json['index'] = mysql_case_info.index
            case_json['status'] = mysql_case_info.status
            case_json['originalCaseId'] = mysql_case_info.originalCaseId

    # 查询是否存在前置条件
    try:
        mysql_casePrecondition_info = model_mysql_casePrecondition.query.filter(
            model_mysql_casePrecondition.caseId == case_id
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_casePrecondition_info is None:
            pass
        else:
            case_json['casePrecondition'] = mysql_casePrecondition_info.content

    # 查询是否存在附件
    try:
        mysql_caseFile_info = model_mysql_caseFile.query.filter(
            model_mysql_caseFile.caseId == case_id, model_mysql_caseFile.status == 1
        ).all()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_caseFile_info is None:
            pass
        else:
            for mqti in mysql_caseFile_info:
                case_json['ossPath'].append({
                    "id": mqti.id,
                    "ossPath": mqti.ossPath,
                    "fileAlias": mqti.fileAlias
                })

    # 查询是否存在测试步骤
    try:
        mysql_caseStep_info = model_mysql_caseStep.query.filter(
            model_mysql_caseStep.caseId == case_id, model_mysql_caseStep.status == 1
        ).all()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_caseStep_info is None:
            pass
        else:
            for mqti in mysql_caseStep_info:
                case_json['caseStep'].append({
                    "id": mqti.id,
                    "content": mqti.content,
                    "expectation": mqti.expectation,
                    "index": mqti.index
                })

    return case_json
