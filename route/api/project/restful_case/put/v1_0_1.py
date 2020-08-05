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
    ['caseId', int, 1, None],
    ['columnId', int, 1, None],
    ['title', str, 1, None],
    ['frontCaseId', int, None, None],
    ['level', int, 1, None],
    ['casePrecondition', str, None, None],
    ['caseStep', list, 0, None],
    ['files', list, 0, None]

)

def key_case_put():
    index=0
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据修改成功",
    "data": None
   }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    case_id = flask.request.json['caseId']
    case_columnId = flask.request.json['columnId']
    case_title= flask.request.json['title']
    case_level = flask.request.json['level']
    front_case = flask.request.json['frontCaseId']
    case_precondition = flask.request.json['casePrecondition']
    case_step = flask.request.json['caseStep']
    files = flask.request.json['files']


    # 查用例是否存在
    try:
        mysql_caseinfo = model_mysql_case.query.filter(
            model_mysql_case.id == case_id,model_mysql_case.type==2,model_mysql_case.status==1
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_caseinfo is None:
            return route.error_msgs[201]['msg_no_case']
        else:
            before_title=mysql_caseinfo.title


    # 查目录是否存在，更新目录
    try:
        mysql_column = model_mysql_case.query.filter(
            model_mysql_case.id == case_columnId,model_mysql_case.type==1,model_mysql_case.status==1
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_column is None:
            return route.error_msgs[201]['msg_no_catalogue']


    #判断必输项title、front_case和level必传
    if len(case_title)==0:
        return route.error_msgs[201]['msg_data_error']
    elif case_level is None:
        return route.error_msgs[201]['msg_data_error']
    elif front_case is None:
        return route.error_msgs[201]['msg_data_error']



    #更新用例主数据
    if front_case==0:
        index=1
        #判断目录是否改变
        if mysql_caseinfo.columnId==case_columnId:
            indexchang2(mysql_caseinfo.index, case_columnId)
            mysql_caseinfo.index = 0
            mysqlpool.session.commit()
            indexchang(index, case_columnId)
        else:
            indexchang(index, case_columnId)

        mysql_caseinfo.index=1
        mysql_caseinfo.title=case_title
        mysql_caseinfo.level=case_level
        mysql_caseinfo.columnId = case_columnId

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
                #*************需要解决往下拖的问题，往上托目前没问题
                index=mysql_front.index+1

                if mysql_caseinfo.columnId == case_columnId:
                    indexchang2(mysql_caseinfo.index, case_columnId)
                    mysql_caseinfo.index=0
                    mysqlpool.session.commit()
                    #重新获取前一个case的排序
                    try:
                        mysql_front = model_mysql_case.query.filter(
                            model_mysql_case.id == front_case, model_mysql_case.type == 2, model_mysql_case.status == 1
                        ).first()
                    except Exception as e:
                        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    index = mysql_front.index + 1

                    indexchang(index, case_columnId)
                else:
                    indexchang(index, case_columnId)

                mysql_caseinfo.index = index
                mysql_caseinfo.title = case_title
                mysql_caseinfo.level = case_level
                mysql_caseinfo.columnId = case_columnId

                mysqlpool.session.commit()



    precondition(mysql_caseinfo.id, case_precondition)
    ossPath(mysql_caseinfo.id, request_user_id,files)
    casestep(mysql_caseinfo.id, case_step, request_user_id)

    # 添加日志

    if before_title==case_title:
        pass
    else:
        case_logs = model_mysql_caseEditLog(
            caseId=mysql_caseinfo.id,
            type=2,
            before=before_title,
            after=case_title
        )
        mysqlpool.session.add(case_logs)
        mysqlpool.session.commit()


    # 最后返回内容
    return response_json

#改变后续的排序
def indexchang(index,columnId):
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
                mqti.index += 1
                mysqlpool.session.commit()
#改变后续的排序
def indexchang2(index,columnId):
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

def precondition(caseid,case_precondition):
    #更新分多种场景
    try:
        case_Precondition = model_mysql_casePrecondition.query.filter(
            model_mysql_casePrecondition.caseId== caseid
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        #原来为空，现在也为空不更新，现在非空则插入数据
        if case_Precondition is None:
            if len(case_precondition)==0:
                pass
            else:
                new_casePrecondition_info = model_mysql_casePrecondition(
                    content=case_precondition,
                    caseId=caseid
                )
                mysqlpool.session.add(new_casePrecondition_info)
                mysqlpool.session.commit()
        else:
            #原来不为空，现在为空/非空直接更新即可
            case_Precondition.content=case_precondition
            mysqlpool.session.commit()


def ossPath(caseid,userID,files):
    if len(files) == 0:
        pass
    else:
        # 需要前端返回附件的id和状态，无id的附件当做新增处理
        for x in files:
            if x['id'] == 0:
                new_caseFile_info = model_mysql_caseFile(
                    ossPath=x['ossPath'],
                    caseId=caseid,
                    status=1,
                    userId=userID,
                    fileAlias=x['fileAlias']

                )
                mysqlpool.session.add(new_caseFile_info)
                mysqlpool.session.commit()

                #获取id
                try:
                    case_file = model_mysql_caseFile.query.filter(
                        model_mysql_caseFile.caseId == caseid,model_mysql_caseFile.ossPath==x['ossPath']
                    ).first()
                except Exception as e:
                    api_logger.error("读取失败，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']
                else:
                    if case_file is None:
                        pass
                    else:
                        # 添加日志
                        case_logs = model_mysql_caseEditLog(
                            caseId=caseid,
                            type=5,
                            before=case_file.id
                        )
                        mysqlpool.session.add(case_logs)
                        mysqlpool.session.commit()

            else:
                try:
                    case_file_info = model_mysql_caseFile.query.filter(
                        model_mysql_caseFile.id == x['id']
                    ).first()
                except Exception as e:
                    api_logger.error("读取失败，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']
                else:
                    if case_file_info is None:
                        pass
                    else:
                        case_file_info.status = x['status']
                        case_file_info.userId = userID
                        mysqlpool.session.commit()
                        if x['status']==-1:
                            # 添加日志
                            case_logs = model_mysql_caseEditLog(
                                caseId=caseid,
                                type=6,
                                before=case_file_info.id
                            )
                            mysqlpool.session.add(case_logs)
                            mysqlpool.session.commit()

def casestep(caseid,case_step,userID):
    lists=[]
    #插入测试步骤
    #这里一定要注意传入数组的参数中千万不能有空格，否则会死都查不出为啥会错，python的json方法无法解析，postman居然可以识别。
    try:
        case_caseStep = model_mysql_caseStep.query.filter(
            model_mysql_caseStep.caseId == caseid,model_mysql_caseStep.status==1
        ).all()

    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        # 原来为空
        if len(case_caseStep)==0:

            #现在也为空
            if len(case_step) == 0:
                pass
            #现在不为空
            else:
                try:
                    for x in case_step:
                        new_caseStep_info = model_mysql_caseStep(
                            index=x['index'],
                            caseId=caseid,
                            content=x['content'],
                            expectation=x['expectation'],
                            status=1,
                            userId=userID
                        )
                        mysqlpool.session.add(new_caseStep_info)
                        mysqlpool.session.commit()
                except Exception as e:
                    api_logger.error("测试数据读取失败，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']
        #原来数据不为空
        else:
            #现在数据为空

            if len(case_step) == 0:
                for x in case_caseStep:
                    x.status=-1
                    x.updateUserId=userID
                    mysqlpool.session.commit()

                # 现在不为空
            else:
                #修改用例需要穿step-id
                try:
                    for x in case_step:
                        lists.append(x['id'])
                        if (x['id']) == 0:
                            new_caseStep_info = model_mysql_caseStep(
                                index=x['index'],
                                caseId=caseid,
                                content=x['content'],
                                expectation=x['expectation'],
                                status=1,
                                userId=userID
                            )
                            mysqlpool.session.add(new_caseStep_info)
                            mysqlpool.session.commit()
                        else:
                            try:
                                case_caseStep_info = model_mysql_caseStep.query.filter(
                                    model_mysql_caseStep.id == x['id'], model_mysql_caseStep.caseId == caseid
                                ).first()
                            except  Exception as e:
                                api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                                return route.error_msgs[500]['msg_db_error']
                            else:
                                if case_caseStep_info is None:
                                    return route.error_msgs[201]['msg_no_casestep']
                                else:
                                    before_content=case_caseStep_info.content
                                    before_expectation=case_caseStep_info.expectation

                                    case_caseStep_info.index = x['index']
                                    case_caseStep_info.content = x['content']
                                    case_caseStep_info.expectation = x['expectation']
                                    case_caseStep_info.status = 1
                                    case_caseStep_info.updateUserId = userID
                                    mysqlpool.session.commit()
                                # 添加日志

                                if before_content ==  x['content']:
                                    pass
                                else:
                                    case_logs = model_mysql_caseEditLog(
                                        caseId=caseid,
                                        type=3,
                                        before=before_content,
                                        after=x['content']
                                    )
                                    mysqlpool.session.add(case_logs)
                                    mysqlpool.session.commit()

                                if before_expectation ==  x['expectation']:
                                    pass
                                else:
                                    case_logs = model_mysql_caseEditLog(
                                        caseId=caseid,
                                        type=4,
                                        before=before_expectation,
                                        after=x['expectation']
                                    )
                                    mysqlpool.session.add(case_logs)
                                    mysqlpool.session.commit()


                except  Exception as e:
                    api_logger.error("读取失败，失败原因：" + repr(e))
                    return route.error_msgs[301]['msg_request_params_illegal']
                #踢出本次删除的步骤
                try:
                    for x in case_caseStep:
                        if x.id not in lists:
                            x.status = -1
                            x.updateUserId = userID
                            mysqlpool.session.commit()
                        else:
                            pass
                except Exception as e:
                    api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']

