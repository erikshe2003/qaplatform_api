# -*- coding: utf-8 -*-

import flask
import re
import datetime
import uuid
import route

from sqlalchemy import or_

from handler.mail import publicmailer
from handler.pool import mysqlpool
from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.config import appconfig
from handler.log import api_logger

from model.mysql import model_mysql_useroperationrecord
from model.mysql import model_mysql_userinfo


# 申请新增账户-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在，排除存在的且为正常的账户/禁用状态的账户
# ----操作
# 3.如果账户不存在，则数据库以及缓存中插入未激活状态的账户数据以及对应的未完成的操作记录
# 4.如果账户存在但状态为未激活，则将先前的账户操作记录数据置为无效，然后插入新的未完成的操作记录
# 5.尝试发送包含账户信息确认页url的邮件
# 6.返回信息给前端
@route.check_post_parameter(
    ['mail_address', str, 1, None]
)
def new_user_info_post():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 取出传入参数值
    requestvalue_mail = flask.request.json["mail_address"]

    # 校验邮箱地址格式
    mail_reg = '^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$'
    if not re.search(mail_reg, requestvalue_mail):
        return route.error_msgs[201]['msg_illegal_format']

    # 2.校验账户是否存在
    try:
        uinfo_mysql = model_mysql_userinfo.query.filter(
            or_(
                model_mysql_userinfo.userEmail == requestvalue_mail,
                model_mysql_userinfo.userNewEmail == requestvalue_mail
            )
        ).first()
    except Exception as e:
        logmsg = "数据库中账户信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
    else:
        if uinfo_mysql is None:
            pass
        elif uinfo_mysql.userStatus == 0:
            pass
        elif uinfo_mysql.userStatus in [-2, -1, 1]:
            return route.error_msgs[201]['msg_mail_exist']
        else:
            return route.error_msgs[201]['msg_status_error']

    # 3.如果账户不存在，则数据库以及缓存中插入未激活状态的账户数据以及对应的未完成的操作记录
    if uinfo_mysql is None:
        # 查询关键操作唯一标识符
        odata = ApiCheck.check_operate(
            appconfig.get("operation_alias", "register")
        )
        if odata["exist"] is True:
            pass
        elif odata["exist"] is False:
            return route.error_msgs[500]['msg_server_error']
        else:
            return route.error_msgs[500]['msg_server_error']

        # 在库中插入账户未激活的信息
        # 先插入mysql
        newuser = model_mysql_userinfo(
            userEmail=requestvalue_mail,
            userStatus=0,
            userAddTime=datetime.datetime.now()
        )
        try:
            mysqlpool.session.add(newuser)
            mysqlpool.session.commit()
        except Exception as e:
            logmsg = "数据库新增账户数据失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return ApiError.requestfail_server(logmsg)

        # 生成操作码
        code = str(
            uuid.uuid3(
                uuid.NAMESPACE_DNS, requestvalue_mail + str(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
        )
        # 发送包含账户信息确认页链接的邮件
        # 先发送邮件，成功后再记录数据
        # 保证过滤掉不存在的邮件地址
        send_result_flag, send_result_type = publicmailer.sendmail_register(
            newuser.userId,
            requestvalue_mail,
            code,
            odata["operationId"]
        )
        print(odata["operationId"])
        # 如果发送失败，则返回错误信息
        if send_result_flag is False:
            if send_result_type == -1:
                return ApiError.requestfail_server("SMTP服务器连接失败")
            elif send_result_type == 1 or send_result_type == 2:
                return ApiError.requestfail_server("公共邮箱登陆失败")
            elif send_result_type == 3:
                return ApiError.requestfail_error("邮件发送失败，请检查邮箱地址")

        # 将操作码数据写入mysql
        insertdata = model_mysql_useroperationrecord(
            userId=newuser.userId,
            operationId=odata["operationId"],
            recordCode=code,
            recordStatus=0,
            recordValidTime=(datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        )
        try:
            mysqlpool.session.add(insertdata)
            mysqlpool.session.commit()
        except Exception as e:
            logmsg = "数据库新增申请账户记录数据失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return ApiError.requestfail_server(logmsg)
    # 4.如果账户存在但状态为未激活，则将先前的账户操作记录数据置为无效，然后插入新的未完成的操作记录
    elif uinfo_mysql.userStatus == 0:
        # 查询关键操作唯一标识符
        odata = ApiCheck.check_operate(
            appconfig.get("operation_alias", "register")
        )
        if odata["exist"] is True:
            pass
        elif odata["exist"] is False:
            return ApiError.requestfail_error("关键操作别名不存在")
        else:
            return ApiError.requestfail_server("操作处理异常")

        # 生成操作码
        code = str(
            uuid.uuid3(
                uuid.NAMESPACE_DNS, requestvalue_mail + str(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
        )
        # 发送包含账户信息确认页链接的邮件
        send_result_flag, send_result_type = publicmailer.sendmail_register(
            uinfo_mysql.userId,
            requestvalue_mail,
            code,
            odata["operationId"]
        )
        # 如果发送失败，则返回错误信息
        if send_result_flag is False:
            if send_result_type == -1:
                return ApiError.requestfail_server("SMTP服务器连接失败")
            elif send_result_type == 1 or send_result_type == 2:
                return ApiError.requestfail_server("公共邮箱登陆失败")
            elif send_result_type == 3:
                return ApiError.requestfail_error("邮件发送失败，请检查邮箱地址")
        # 查询mysql中的操作记录
        try:
            rdata_mysql = model_mysql_useroperationrecord.query.filter_by(
                userId=uinfo_mysql.userId,
                operationId=odata["operationId"],
                recordStatus=0
            ).all()
        except Exception as e:
            logmsg = "账户操作记录数据查询失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return ApiError.requestfail_server(logmsg)
        # 如果查询到了，则全部置为无效
        if rdata_mysql is not None:
            for d in rdata_mysql:
                d.recordStatus = -1
            try:
                mysqlpool.session.commit()
            except Exception as e:
                logmsg = "账户操作记录数据更新失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                return ApiError.requestfail_server(logmsg)
        # 将新操作码数据写入mysql
        insertdata = model_mysql_useroperationrecord(
            userId=uinfo_mysql.userId,
            operationId=odata["operationId"],
            recordCode=code,
            recordStatus=0,
            recordValidTime=(datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        )
        try:
            mysqlpool.session.add(insertdata)
            mysqlpool.session.commit()
        except Exception as e:
            logmsg = "账户操作记录数据新增失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return ApiError.requestfail_server(logmsg)
    # 5.如果账户存在且状态不为未激活，则将告知前端账户已存在
    else:
        return ApiError.requestfail_error("账户已存在")
    # 定义msg
    response_json["error_msg"] = "操作成功，请查收账户注册邮件"
    # 最后返回内容
    return response_json
