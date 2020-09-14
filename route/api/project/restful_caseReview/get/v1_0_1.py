# -*- coding: utf-8 -*-

import flask

import route


from handler.log import api_logger
from model.mysql import model_mysql_case
from model.mysql import model_mysql_userinfo
from model.mysql import model_mysql_project
from model.mysql import model_mysql_projectMember
from model.mysql import model_mysql_projectReviewRecord
from model.mysql import model_mysql_casePrecondition
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
@route.check_get_parameter(
    ['projectId', int, 1, None],
    ['stat', int, -1, None],
    ['initiatorId', int, 0, None]
)
def key_caseReview_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据获取成功",
        "data": []
    }


    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    project_id = flask.request.args['projectId']
    initiator_id = flask.request.args['initiatorId']
    stat = flask.request.args['stat']
    # 判断项目是否存在，并获取仓库id
    try:
        mysql_project_info = model_mysql_project.query.filter(
            model_mysql_project.id == project_id,model_mysql_project.status==1
        ).first()
    except Exception as e:

        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_project_info is None:
            return route.error_msgs[201]['msg_no_project']

    #判断当前用户是否在项目中
    try:
        mysql_member_info = model_mysql_projectMember.query.filter(
            model_mysql_projectMember.projectId == project_id,model_mysql_projectMember.userId==request_user_id
        ).first()
    except Exception as e:

        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_member_info is None:
            return route.error_msgs[201]['msg_no_projectmember']


    #查询满足条件的记录
    if int(stat)==-1 and  int(initiator_id)==0:

        try:
            mysql_reviews_info = model_mysql_projectReviewRecord.query.filter(
                model_mysql_projectReviewRecord.projectId == project_id,
                model_mysql_projectReviewRecord.reviewerId == request_user_id,

            ).order_by(model_mysql_projectReviewRecord.createTime).all()

        except Exception as e:

            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_reviews_info is None:
                return route.error_msgs[201]['msg_no_projectmember']
            else:
                for mqti in mysql_reviews_info:
                    # 获取发起人信息
                    try:
                        user_info = model_mysql_userinfo.query.filter(
                            model_mysql_userinfo.userId == mqti.initiatorId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if user_info is None:
                            return route.error_msgs[201]['msg_no_auth']
                        else:
                            user_name = user_info.userNickName

                    # 获取测试用例树

                    try:
                        mysql_case_info = model_mysql_case.query.filter(
                            model_mysql_case.id == mqti.caseId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_case_info is None:
                            return route.error_msgs[201]['msg_no_case']
                        else:
                            case_info={
                                'id': mysql_case_info.id,
                                'columnId': mysql_case_info.columnId,
                                'title': mysql_case_info.title,
                                'level': mysql_case_info.level,
                                'index': mysql_case_info.index,
                                'veri': mysql_case_info.veri,
                                'status': mysql_case_info.status,
                                'arch': mysql_case_info.arch,
                                'casePrecondition': None,
                                'ossPath': [],
                                'caseStep': []

                            }

                    # 查询是否存在前置条件
                    try:
                        mysql_casePrecondition_info = model_mysql_casePrecondition.query.filter(
                            model_mysql_casePrecondition.caseId == mqti.caseId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_casePrecondition_info is None:
                            pass
                        else:
                            case_info['casePrecondition'] = mysql_casePrecondition_info.content

                    # 查询是否存在附件
                    try:
                        mysql_caseFile_info = model_mysql_caseFile.query.filter(
                            model_mysql_caseFile.caseId == mqti.caseId, model_mysql_caseFile.status == 1
                        ).all()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_caseFile_info is None:
                            pass
                        else:
                            for mqti1 in mysql_caseFile_info:
                                case_info['ossPath'].append({
                                    "id": mqti1.id,
                                    "ossPath": mqti1.ossPath,
                                    "fileAlias": mqti1.fileAlias
                                })

                    # 查询是否存在测试步骤
                    try:
                        mysql_caseStep_info = model_mysql_caseStep.query.filter(
                            model_mysql_caseStep.caseId == mqti.caseId, model_mysql_caseStep.status == 1
                        ).order_by(model_mysql_caseStep.index).all()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_caseStep_info is None:
                            pass
                        else:
                            for mqti2 in mysql_caseStep_info:
                                case_info['caseStep'].append({
                                    "id": mqti2.id,
                                    "content": mqti2.content,
                                    "expectation": mqti2.expectation,
                                    "index": mqti2.index
                                })




                    # 构造返回信息
                    response_json['data'].append({
                        "id": mqti.id,
                        "caseInfo": case_info,
                        "result": mqti.result,
                        "createTime": str(mqti.createTime),
                        "finishTime": str(mqti.finishTime),
                        "initiator": user_name
                    })
    elif int(stat)==-1 and int(initiator_id)!=0:
        try:
            mysql_reviews_info = model_mysql_projectReviewRecord.query.filter(
                model_mysql_projectReviewRecord.projectId == project_id,
                model_mysql_projectReviewRecord.reviewerId == request_user_id,
                model_mysql_projectReviewRecord.initiatorId==initiator_id
            ).order_by(model_mysql_projectReviewRecord.createTime).all()
        except Exception as e:

            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_reviews_info is None:
                return route.error_msgs[201]['msg_no_projectmember']
            else:
                for mqti in mysql_reviews_info:

                    # 获取测试用例title
                    # 获取测试用例树

                    try:
                        mysql_case_info = model_mysql_case.query.filter(
                            model_mysql_case.id == mqti.caseId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_case_info is None:
                            return route.error_msgs[201]['msg_no_case']
                        else:
                            case_info={
                                'id': mysql_case_info.id,
                                'columnId': mysql_case_info.columnId,
                                'title': mysql_case_info.title,
                                'level': mysql_case_info.level,
                                'index': mysql_case_info.index,
                                'veri': mysql_case_info.veri,
                                'status': mysql_case_info.status,
                                'arch': mysql_case_info.arch,
                                'casePrecondition': None,
                                'ossPath': [],
                                'caseStep': []

                            }

                    # 查询是否存在前置条件
                    try:
                        mysql_casePrecondition_info = model_mysql_casePrecondition.query.filter(
                            model_mysql_casePrecondition.caseId == mqti.caseId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_casePrecondition_info is None:
                            pass
                        else:
                            case_info['casePrecondition'] = mysql_casePrecondition_info.content

                    # 查询是否存在附件
                    try:
                        mysql_caseFile_info = model_mysql_caseFile.query.filter(
                            model_mysql_caseFile.caseId == mqti.caseId, model_mysql_caseFile.status == 1
                        ).all()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_caseFile_info is None:
                            pass
                        else:
                            for mqti1 in mysql_caseFile_info:
                                case_info['ossPath'].append({
                                    "id": mqti1.id,
                                    "ossPath": mqti1.ossPath,
                                    "fileAlias": mqti1.fileAlias
                                })

                    # 查询是否存在测试步骤
                    try:
                        mysql_caseStep_info = model_mysql_caseStep.query.filter(
                            model_mysql_caseStep.caseId == mqti.caseId, model_mysql_caseStep.status == 1
                        ).order_by(model_mysql_caseStep.index).all()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_caseStep_info is None:
                            pass
                        else:
                            for mqti2 in mysql_caseStep_info:
                                case_info['caseStep'].append({
                                    "id": mqti2.id,
                                    "content": mqti2.content,
                                    "expectation": mqti2.expectation,
                                    "index": mqti2.index
                                })


                    # 获取发起人信息
                    try:
                        mysql_user_info = model_mysql_userinfo.query.filter(
                            model_mysql_userinfo.userId == mqti.initiatorId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_user_info is None:
                            return route.error_msgs[201]['msg_no_auth']
                        else:
                            user_name = mysql_user_info.userNickName

                    # 构造返回信息
                    response_json['data'].append({
                        "id": mqti.id,
                        "caseInfo": case_info,
                        "result": mqti.result,
                        "createTime": str(mqti.createTime),
                        "finishTime": str(mqti.finishTime),
                        "initiator": user_name
                    })

    elif int(stat) != -1 and int(initiator_id) == 0:
        try:
            mysql_reviews_info = model_mysql_projectReviewRecord.query.filter(
                model_mysql_projectReviewRecord.projectId == project_id,
                model_mysql_projectReviewRecord.reviewerId == request_user_id,
                model_mysql_projectReviewRecord.result==stat
            ).order_by(model_mysql_projectReviewRecord.createTime).all()
        except Exception as e:

            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_reviews_info is None:
                return route.error_msgs[201]['msg_no_projectmember']
            else:
                for mqti in mysql_reviews_info:

                    # 获取测试用例title
                    # 获取测试用例树

                    try:
                        mysql_case_info = model_mysql_case.query.filter(
                            model_mysql_case.id == mqti.caseId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_case_info is None:
                            return route.error_msgs[201]['msg_no_case']
                        else:
                            case_info={
                                'id': mysql_case_info.id,
                                'columnId': mysql_case_info.columnId,
                                'title': mysql_case_info.title,
                                'level': mysql_case_info.level,
                                'index': mysql_case_info.index,
                                'veri': mysql_case_info.veri,
                                'status': mysql_case_info.status,
                                'arch': mysql_case_info.arch,
                                'casePrecondition': None,
                                'ossPath': [],
                                'caseStep': []

                            }

                    # 查询是否存在前置条件
                    try:
                        mysql_casePrecondition_info = model_mysql_casePrecondition.query.filter(
                            model_mysql_casePrecondition.caseId == mqti.caseId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_casePrecondition_info is None:
                            pass
                        else:
                            case_info['casePrecondition'] = mysql_casePrecondition_info.content

                    # 查询是否存在附件
                    try:
                        mysql_caseFile_info = model_mysql_caseFile.query.filter(
                            model_mysql_caseFile.caseId == mqti.caseId, model_mysql_caseFile.status == 1
                        ).all()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_caseFile_info is None:
                            pass
                        else:
                            for mqti1 in mysql_caseFile_info:
                                case_info['ossPath'].append({
                                    "id": mqti1.id,
                                    "ossPath": mqti1.ossPath,
                                    "fileAlias": mqti1.fileAlias
                                })

                    # 查询是否存在测试步骤
                    try:
                        mysql_caseStep_info = model_mysql_caseStep.query.filter(
                            model_mysql_caseStep.caseId == mqti.caseId, model_mysql_caseStep.status == 1
                        ).order_by(model_mysql_caseStep.index).all()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_caseStep_info is None:
                            pass
                        else:
                            for mqti2 in mysql_caseStep_info:
                                case_info['caseStep'].append({
                                    "id": mqti2.id,
                                    "content": mqti2.content,
                                    "expectation": mqti2.expectation,
                                    "index": mqti2.index
                                })


                    # 获取发起人信息
                    try:
                        mysql_user_info = model_mysql_userinfo.query.filter(
                            model_mysql_userinfo.userId == mqti.initiatorId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_user_info is None:
                            return route.error_msgs[201]['msg_no_auth']
                        else:
                            user_name = mysql_user_info.userNickName

                    # 构造返回信息
                    response_json['data'].append({
                        "id": mqti.id,
                        "caseInfo": case_info,
                        "result": mqti.result,
                        "createTime": str(mqti.createTime),
                        "finishTime": str(mqti.finishTime),
                        "initiator": user_name
                    })

    elif int(stat) != -1 and int(initiator_id) != 0:
        try:
            mysql_reviews_info = model_mysql_projectReviewRecord.query.filter(
                model_mysql_projectReviewRecord.projectId == project_id,
                model_mysql_projectReviewRecord.reviewerId == request_user_id,
                model_mysql_projectReviewRecord.result==stat,
                model_mysql_projectReviewRecord.initiatorId==initiator_id
            ).order_by(model_mysql_projectReviewRecord.createTime).all()
        except Exception as e:

            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_reviews_info is None:
                return route.error_msgs[201]['msg_no_projectmember']
            else:
                for mqti in mysql_reviews_info:

                    # 获取测试用例title
                    # 获取测试用例树

                    try:
                        mysql_case_info = model_mysql_case.query.filter(
                            model_mysql_case.id == mqti.caseId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_case_info is None:
                            return route.error_msgs[201]['msg_no_case']
                        else:
                            case_info={
                                'id': mysql_case_info.id,
                                'columnId': mysql_case_info.columnId,
                                'title': mysql_case_info.title,
                                'level': mysql_case_info.level,
                                'index': mysql_case_info.index,
                                'veri': mysql_case_info.veri,
                                'status': mysql_case_info.status,
                                'arch': mysql_case_info.arch,
                                'casePrecondition': None,
                                'ossPath': [],
                                'caseStep': []

                            }

                    # 查询是否存在前置条件
                    try:
                        mysql_casePrecondition_info = model_mysql_casePrecondition.query.filter(
                            model_mysql_casePrecondition.caseId == mqti.caseId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_casePrecondition_info is None:
                            pass
                        else:
                            case_info['casePrecondition'] = mysql_casePrecondition_info.content

                    # 查询是否存在附件
                    try:
                        mysql_caseFile_info = model_mysql_caseFile.query.filter(
                            model_mysql_caseFile.caseId == mqti.caseId, model_mysql_caseFile.status == 1
                        ).all()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_caseFile_info is None:
                            pass
                        else:
                            for mqti1 in mysql_caseFile_info:
                                case_info['ossPath'].append({
                                    "id": mqti1.id,
                                    "ossPath": mqti1.ossPath,
                                    "fileAlias": mqti1.fileAlias
                                })

                    # 查询是否存在测试步骤
                    try:
                        mysql_caseStep_info = model_mysql_caseStep.query.filter(
                            model_mysql_caseStep.caseId == mqti.caseId, model_mysql_caseStep.status == 1
                        ).order_by(model_mysql_caseStep.index).all()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_caseStep_info is None:
                            pass
                        else:
                            for mqti2 in mysql_caseStep_info:
                                case_info['caseStep'].append({
                                    "id": mqti2.id,
                                    "content": mqti2.content,
                                    "expectation": mqti2.expectation,
                                    "index": mqti2.index
                                })


                    # 获取发起人信息
                    try:
                        mysql_user_info = model_mysql_userinfo.query.filter(
                            model_mysql_userinfo.userId == mqti.initiatorId
                        ).first()
                    except Exception as e:
                        api_logger.error("读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        if mysql_user_info is None:
                            return route.error_msgs[201]['msg_no_auth']
                        else:
                            user_name = mysql_user_info.userNickName

                    # 构造返回信息
                    response_json['data'].append({
                        "id": mqti.id,
                        "caseInfo": case_info,
                        "result": mqti.result,
                        "createTime": str(mqti.createTime),
                        "finishTime": str(mqti.finishTime),
                        "initiator": user_name
                    })

    return response_json