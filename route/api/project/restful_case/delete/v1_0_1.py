# -*- coding: utf-8 -*-

import flask
import route
import datetime

from handler.pool import mysqlpool
from handler.log import api_logger

from model.mysql import model_mysql_caseEditLog
from model.mysql import model_mysql_casePrecondition
from model.mysql import model_mysql_case
from model.mysql import model_mysql_caseFile
from model.mysql import model_mysql_caseStep


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
    case_id = int(flask.request.args['id'])
    project_id = int(flask.request.args['projectId'])

    # 获取用例的全部信息
    try:
        mysql_case_info = model_mysql_case.query.filter(
            model_mysql_case.id == case_id,
            model_mysql_case.type == 2
        ).first()
    except Exception as e:
        api_logger.error("用例数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_case_info is None:
            return route.error_msgs[201]['msg_no_case']

    # 待删除用例无法再次删除
    if mysql_case_info.status == 3 or mysql_case_info.veri == 1:
        return route.error_msgs[201]['msg_case_already_to_be_deleted']

    # 判断是否是仓库的用例
    # 若是本项目的测试用例
    if mysql_case_info.projectId == project_id:
        # 若为项目新增用例
        if mysql_case_info.originalCaseId == 0:
            # 需要判断用例是否通过评审，已通过评审的用例要重新评审才可以删除
            if mysql_case_info.veri != 3:
                # 当前项目 && originalCaseId == 0 && veri in (0,1,2)
                # 删除用例
                mysql_case_info.status = -1
                mysql_case_info.updateUserId = request_user_id
                mysql_case_info.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                # 添加日志
                mysqlpool.session.add(model_mysql_caseEditLog(
                    caseId=mysql_case_info.id,
                    type=7
                ))
                try:
                    mysqlpool.session.commit()
                    api_logger.error("用例删除成功")
                except Exception as e:
                    api_logger.error("用例删除失败，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']
            else:
                mysql_case_info.status = 3
                mysql_case_info.updateUserId = request_user_id
                mysql_case_info.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                mysql_case_info.veri = 0
                # 添加日志
                mysqlpool.session.add(model_mysql_caseEditLog(
                    caseId=mysql_case_info.id,
                    type=7
                ))
                try:
                    mysqlpool.session.commit()
                    api_logger.error("用例删除成功")
                except Exception as e:
                    api_logger.error("用例删除失败，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']
        # 若非项目新增用例
        else:
            mysql_case_info.status = 3
            mysql_case_info.updateUserId = request_user_id
            mysql_case_info.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            mysql_case_info.veri = 0
            # 添加日志
            mysqlpool.session.add(model_mysql_caseEditLog(
                caseId=mysql_case_info.id,
                type=7
            ))
            try:
                mysqlpool.session.commit()
                api_logger.error("用例删除成功")
            except Exception as e:
                api_logger.error("用例删除失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
    # 若非本项目的测试用例
    else:
        # 后台新增一条用例caseId自增、且内容与被删除用例数据一致，其originalCaseId为被删除的用例的caseId
        # 复制case
        mysql_new_case = model_mysql_case(
            title=mysql_case_info.title,
            depositoryId=mysql_case_info.depositoryId,
            projectId=mysql_case_info.projectId,
            columnId=mysql_case_info.columnId,
            index=mysql_case_info.index,
            columnLevel=mysql_case_info.columnLevel,
            level=mysql_case_info.level,
            type=mysql_case_info.type,
            status=3,
            userId=mysql_case_info.userId,
            createTime=mysql_case_info.createTime,
            updateUserId=mysql_case_info.updateUserId,
            updateTime=mysql_case_info.updateTime,
            veri=0,
            arch=mysql_case_info.arch,
            originalCaseId=mysql_case_info.id,
        )
        mysqlpool.session.add(mysql_new_case)
        try:
            mysqlpool.session.commit()
        except Exception as e:
            api_logger.error("用例复制失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']

        # 复制precondition
        try:
            mysql_case_precondition_info = model_mysql_casePrecondition.query.filter(
                model_mysql_casePrecondition.caseId == case_id
            ).first()
        except Exception as e:
            api_logger.error("用例期望结果读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_case_precondition_info is not None:
                mysqlpool.session.add(model_mysql_casePrecondition(
                    content=mysql_case_precondition_info.content,
                    caseId=mysql_new_case.id,
                    createTime=mysql_case_precondition_info.createTime,
                    updateTime=mysql_case_precondition_info.updateTime,
                ))
        # 复制steps
        try:
            mysql_case_steps_info = model_mysql_caseStep.query.filter(
                model_mysql_caseStep.caseId == case_id
            ).order_by(
                model_mysql_caseStep.index
            ).all()
        except Exception as e:
            api_logger.error("用例步骤数据读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            for mcsi in mysql_case_steps_info:
                mysqlpool.session.add(model_mysql_caseStep(
                    caseId=mysql_new_case.id,
                    index=mcsi.index,
                    content=mcsi.content,
                    expectation=mcsi.expectation,
                    status=mcsi.status,
                    userId=mcsi.userId,
                    createTime=mcsi.createTime,
                    updateUserId=mcsi.updateUserId,
                    updateTime=mcsi.updateTime,
                ))
        # 复制files
        try:
            mysql_case_files_info = model_mysql_caseFile.query.filter(
                model_mysql_caseFile.caseId == case_id
            ).all()
        except Exception as e:
            api_logger.error("用例附件数据读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            for mcfi in mysql_case_files_info:
                mysqlpool.session.add(model_mysql_caseFile(
                    caseId=mysql_new_case.id,
                    ossPath=mcfi.ossPath,
                    fileAlias=mcfi.fileAlias,
                    status=mcfi.status,
                    userId=mcfi.userId,
                    createTime=mcfi.createTime,
                ))
        # 复制logs
        try:
            mysql_case_logs_info = model_mysql_caseEditLog.query.filter(
                model_mysql_caseEditLog.caseId == case_id
            ).all()
        except Exception as e:
            api_logger.error("用例编辑日志数据读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            for mcli in mysql_case_logs_info:
                mysqlpool.session.add(model_mysql_caseEditLog(
                    caseId=mysql_new_case.id,
                    type=mcli.type,
                    before=mcli.before,
                    after=mcli.after,
                    createTime=mcli.createTime,
                ))

        # 添加日志
        mysqlpool.session.add(model_mysql_caseEditLog(
            caseId=mysql_new_case.id,
            type=1
        ))

        try:
            mysqlpool.session.commit()
            api_logger.error("用例克隆并预删除成功")
        except Exception as e:
            api_logger.error("用例克隆并预删除失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']

    return response_json
