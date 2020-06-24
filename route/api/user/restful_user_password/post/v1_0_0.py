# -*- coding: utf-8 -*-

import flask
import route

from handler.mail import publicmailer
from handler.log import api_logger
from handler.pool import mysqlpool
from handler.api.error import ApiError
from handler.api.check import ApiCheck

from model.mysql import model_mysql_useroperationrecord, model_mysql_userinfo


# 账户重置密码-api路由
# ----校验
# 1.校验传参
# 2.校验账户状态
# 3.校验操作类型和操作码
# ----操作
# 4.重置密码
# 5.将重置密码的记录置为无效
# 6.发送重置密码成功邮件
@route.check_post_parameter(
    ['user_id', int, 1, None],
    ['record_code', str, 1, 100],
    ['operation_id', int, 1, None],
    ['new_password', str, 1, 100]
)
def user_password_post():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 校验通过后赋值
    requestvalue_userid = flask.request.json["user_id"]
    requestvalue_recordcode = flask.request.json["record_code"]
    requestvalue_operationid = flask.request.json["operation_id"]
    requestvalue_password = flask.request.json["new_password"]

    # 2.校验账户状态
    userdata = ApiCheck.check_user(requestvalue_userid)
    if userdata["exist"] is False:
        return ApiError.requestfail_error("账户不存在")
    elif userdata["exist"] is True and userdata["userStatus"] == 1:
        pass
    elif userdata["exist"] is True and userdata["userStatus"] == 0:
        return ApiError.requestfail_error("账户未激活")
    elif userdata["exist"] is True and userdata["userStatus"] == -1:
        return ApiError.requestfail_error("账户已禁用")
    else:
        return ApiError.requestfail_error("账户信息校验异常")

    # 3.校验操作类型和操作码
    codeexist, codevalid = ApiCheck.check_code(
        userdata["userId"],
        requestvalue_recordcode,
        requestvalue_operationid
    )
    if codeexist is False:
        return ApiError.requestfail_error("操作码错误或不存在")
    elif codeexist is True and codevalid == 0:
        return ApiError.requestfail_error("操作码过期")
    elif codeexist is True and codevalid == 1:
        pass
    else:
        return ApiError.requestfail_server("操作码校验异常")

    # 4.重置密码
    # 先修改mysql中的登录密码
    try:
        uinfo_mysql = model_mysql_userinfo.query.filter_by(userId=userdata["userId"]).first()
    except Exception as e:
        logmsg = "mysql中账户信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    uinfo_mysql.userPassword = requestvalue_password
    try:
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "mysql中账户密码更新失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)

    # 5.将重置密码的记录置为已完成
    try:
        uodata = model_mysql_useroperationrecord.query.filter_by(
            userId=userdata["userId"],
            operationId=requestvalue_operationid,
            recordStatus=0
        ).first()
    except Exception as e:
        logmsg = "mysql中账户操作记录读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    uodata.recordStatus = 1
    try:
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "mysql中账户操作记录更新失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)

    # 6.发送重置密码成功邮件
    publicmailer.sendmail_reset_password_success(
        uinfo_mysql.userEmail
    )
    # 定义msg
    response_json["error_msg"] = "操作成功，请查收重置密码邮件"
    # 最后返回内容
    return response_json