# -*- coding: utf-8 -*-

import flask
import time
import route

from handler.pool import mysqlpool

from handler.log import api_logger

from model.mysql import model_mysql_depositoryProjectFiledOrg
from model.mysql import model_mysql_case
from model.mysql import model_mysql_project
from model.mysql import model_mysql_projectMember
from model.mysql import model_mysql_projectArchivePendingCase

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断项目是否存在
            自动进行归档
            添加归档记录
            返回操作结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(

    ['id', int, None, None]
)
def key_projectArchive_post():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "提交成功",
        "data": None
    }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    project_id = flask.request.json['id']

    # 判断项目是否存在
    try:
        mysql_project_info = model_mysql_project.query.filter(
            model_mysql_project.id == project_id,
            model_mysql_project.status == 1

        ).first()
    except Exception as e:
        api_logger.error("数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_project_info is None:
            return route.error_msgs[201]['msg_no_subject']
    # 判断是否存在归档中的同仓库项目
    try:
        mysql_exitdepositoryarc = model_mysql_depositoryProjectFiledOrg.query.filter(
            model_mysql_depositoryProjectFiledOrg.depositoryId == mysql_project_info.depositoryId,
            model_mysql_depositoryProjectFiledOrg.result == 1

        ).first()
    except Exception as e:
        api_logger.error("数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_exitdepositoryarc is None:
            pass
        else:
            return route.error_msgs[201]['msg_exist_depositoryarc']

    # 判断用户是否拥有归档权限
    try:
        mysql_projectMember_info = model_mysql_projectMember.query.filter(
            model_mysql_projectMember.projectId == project_id,
            model_mysql_projectMember.userId == request_user_id,
            model_mysql_projectMember.type == 1

        ).first()
    except Exception as e:
        api_logger.error("数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_projectMember_info is None:
            return route.error_msgs[201]['msg_no_auth']

    # 自动归档逻辑
    # 判断是否已经发起过归档

    try:
        mysql_acr_info = model_mysql_depositoryProjectFiledOrg.query.filter(
            model_mysql_depositoryProjectFiledOrg.projectId == project_id,
            model_mysql_depositoryProjectFiledOrg.depositoryId == mysql_project_info.depositoryId,
            model_mysql_depositoryProjectFiledOrg.result == 1

        ).first()
    except Exception as e:
        api_logger.error("数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_acr_info is None:
            pass
        else:
            return route.error_msgs[201]['msg_exit_arcrecode']

    # 发起归档
    start_depositoryProjectFiledOrg = model_mysql_depositoryProjectFiledOrg(
        depositoryId=mysql_project_info.depositoryId,
        projectId=project_id,
        result=1
    )

    mysqlpool.session.add(start_depositoryProjectFiledOrg)
    mysqlpool.session.commit()
    # 获取归档记录id
    try:
        mysql_arc_record = model_mysql_depositoryProjectFiledOrg.query.filter(
            model_mysql_depositoryProjectFiledOrg.projectId == project_id,
            model_mysql_depositoryProjectFiledOrg.depositoryId == mysql_project_info.depositoryId,
            model_mysql_depositoryProjectFiledOrg.result == 1

        ).first()
    except Exception as e:
        api_logger.error("数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_arc_record is None:
            return route.error_msgs[201]['msg_no_arcrecode']

    # 调用归档方法
    mysql_project_info.status = 2
    mysqlpool.session.commit()

    flag=autoarchive(project_id)

    # 归档结束
    if flag==0:
        mysql_project_info.status = 3
        mysql_arc_record.result = 2
    else:
        mysql_project_info.status = 2
        mysql_arc_record.result = 1

    mysqlpool.session.commit()

    return response_json


def autoarchive(projectId):
    count=0
    # 查询新增的用例，直接通过
    try:
        mysql_case1_id = model_mysql_case.query.filter(
            model_mysql_case.projectId == projectId,
            model_mysql_case.originalCaseId == 0,
            model_mysql_case.veri == 3,
            model_mysql_case.status == 1
        ).all()
    except Exception as e:

        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_case1_id is None:
            pass
        else:
            for mqti1 in mysql_case1_id:
                mqti1.arch = 2
                mysqlpool.session.commit()

    # 查询编辑过得用例

    try:
        mysql_case2_id = model_mysql_case.query.filter(
            model_mysql_case.projectId == projectId,
            model_mysql_case.originalCaseId != 0,
            model_mysql_case.veri == 3,
            model_mysql_case.status == 1
        ).all()
    except Exception as e:

        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_case2_id is None:
            pass
        else:
            for mqti2 in mysql_case2_id:
                # 将仓库用例设置为失效，如果存在冲突用例计入冲突记录表
                try:
                    mysql_case3_id = model_mysql_case.query.filter(
                        model_mysql_case.id == mqti2.originalCaseId
                    ).first()

                except Exception as e:

                    api_logger.error("读取失败，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']
                else:
                    if mysql_case3_id is None:
                        mqti2.arch = 2
                        mysqlpool.session.commit()
                    else:
                        if mysql_case3_id.status == 1:
                            mysql_case3_id.status = 2
                            mqti2.arch = 2
                            mysqlpool.session.commit()

                        else:
                            # 查询最后一次归档记录
                            try:
                                mysql_last = model_mysql_depositoryProjectFiledOrg.query.filter(
                                    model_mysql_depositoryProjectFiledOrg.depositoryId == mysql_case3_id.depositoryId,
                                    model_mysql_depositoryProjectFiledOrg.result == 2
                                ).order_by(model_mysql_depositoryProjectFiledOrg.id.desc()).first()

                            except Exception as e:

                                api_logger.error("读取失败，失败原因：" + repr(e))
                                return route.error_msgs[500]['msg_db_error']
                            else:

                                if mysql_last is None:

                                    continue
                                else:

                                    # 查询other的用例id
                                    try:
                                        mysql_other = model_mysql_case.query.filter(
                                            model_mysql_case.projectId == mysql_last.projectId,
                                            model_mysql_case.depositoryId == mysql_last.depositoryId,
                                            model_mysql_case.originalCaseId == mysql_case3_id.id
                                        ).first()
                                    except Exception as e:

                                        api_logger.error("读取失败，失败原因：" + repr(e))
                                        return route.error_msgs[500]['msg_db_error']
                                    else:

                                        if mysql_other is None:

                                            continue
                                        else:

                                            # 冲突记录


                                            new_pend1 = model_mysql_projectArchivePendingCase(
                                                projectId=projectId,
                                                originalCaseId=mysql_case3_id.id,
                                                projectIdCaseId=mqti2.id,
                                                otherCaseId=mysql_other.id,
                                                status=1
                                            )
                                            mysqlpool.session.add(new_pend1)
                                            mysqlpool.session.commit()
                                            count+=1


    # 查询仓库中被删除且审核通过的用例

    try:
        mysql_case4_id = model_mysql_case.query.filter(
            model_mysql_case.projectId == projectId,
            model_mysql_case.originalCaseId != 0,
            model_mysql_case.veri == 3,
            model_mysql_case.status == 3
        ).all()
    except Exception as e:

        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_case4_id is None:
            pass
        else:
            for mqti4 in mysql_case4_id:
                # 将仓库用例设置为已删除，如果存在冲突用例计入冲突记录表
                try:
                    mysql_case5_id = model_mysql_case.query.filter(
                        model_mysql_case.id == mqti4.originalCaseId
                    ).first()

                except Exception as e:

                    api_logger.error("读取失败，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']
                else:
                    if mysql_case5_id is None:
                        mqti4.arch = 2
                        mqti4.status = -1
                        mysqlpool.session.commit()
                    else:
                        if mysql_case5_id.status == 1:
                            mysql_case5_id.status = -1
                            mqti4.arch = 2
                            mqti4.status = -1
                            mysqlpool.session.commit()

                        else:
                            # 查询最后一次修改记录
                            try:
                                mysql_last2 = model_mysql_depositoryProjectFiledOrg.query.filter(
                                    model_mysql_depositoryProjectFiledOrg.depositoryId == mysql_case5_id.depositoryId,
                                    model_mysql_depositoryProjectFiledOrg.result == 2
                                ).order_by(model_mysql_depositoryProjectFiledOrg.id.desc()).first()

                            except Exception as e:

                                api_logger.error("读取失败，失败原因：" + repr(e))
                                return route.error_msgs[500]['msg_db_error']
                            else:
                                if mysql_last2 is None:
                                    continue
                                else:
                                    # 查询other的用例id
                                    try:
                                        mysql_other2 = model_mysql_case.query.filter(
                                            model_mysql_case.projectId == mysql_last2.projectId,
                                            model_mysql_case.depositoryId == mysql_last2.depositoryId,
                                            model_mysql_case.originalCaseId == mysql_case5_id.id
                                        ).first()
                                    except Exception as e:

                                        api_logger.error("读取失败，失败原因：" + repr(e))
                                        return route.error_msgs[500]['msg_db_error']
                                    else:

                                        if mysql_other2 is None:
                                            continue
                                        else:
                                            # 冲突记录
                                            new_pend2 = model_mysql_projectArchivePendingCase(
                                                projectId=projectId,
                                                originalCaseId=mysql_case5_id.id,
                                                projectIdCaseId=mqti4.id,
                                                otherCaseId=mysql_other2.id,
                                                status=1

                                            )
                                            mysqlpool.session.add(new_pend2)
                                            mysqlpool.session.commit()
                                            count += 1
    return count
