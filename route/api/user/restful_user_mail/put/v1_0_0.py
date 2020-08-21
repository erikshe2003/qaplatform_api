# -*- coding: utf-8 -*-

import flask
import re
import route

from handler.mail import publicmailer
from handler.log import api_logger
from handler.pool import mysqlpool
from handler.api.error import ApiError
from handler.api.check import ApiCheck

from model.mysql import model_mysql_useroperationrecord
from model.mysql import model_mysql_userinfo


@route.check_post_parameter(
    ['user_id', int, 1, None],
    ['mail_address', str, 1, 100],
    ['new_mail_address', str, 1, 100],
    ['record_code', str, 1, 100],
    ['operation_id', int, 0, None]
)
def user_mail_put():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 校验通过后赋值
    requestvalue_userid = flask.request.json["user_id"]
    requestvalue_mail = flask.request.json["mail_address"]
    requestvalue_newmail = flask.request.json["new_mail_address"]
    requestvalue_recordcode = flask.request.json["record_code"]
    requestvalue_operationid = flask.request.json["operation_id"]

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
        requestvalue_userid,
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

    # 6.校验所修改邮箱地址是否正确
    try:
        uinfo_mysql = model_mysql_userinfo.query.filter_by(userId=requestvalue_userid).first()
    except Exception as e:
        logmsg = "mysql中账户信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
    if uinfo_mysql.userNewEmail == requestvalue_newmail:
        pass
    else:
        return ApiError.requestfail_error("新邮箱地址错误")

    # 8.修改所旧邮箱为新邮箱，然后清空新邮箱记录
    uinfo_mysql.userEmail = requestvalue_newmail
    uinfo_mysql.userNewEmail = None
    try:
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "mysql中账户邮箱绑定数据更新失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']

    # 11.将修改绑定邮箱的记录修改为已完成
    try:
        uodata = model_mysql_useroperationrecord.query.filter_by(
            userId=userdata["userId"],
            operationId=requestvalue_operationid,
            recordStatus=0
        ).first()
        uodata.recordStatus = 1
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "mysql中账户操作记录更新失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']

    # 12.发送修改绑定邮箱成功邮件
    publicmailer.sendmail_changemail_success(
        requestvalue_newmail
    )
    # 定义msg
    response_json["error_msg"] = "操作成功，请到新邮箱中查收修改成功邮件"
    # 最后返回内容
    return response_json
