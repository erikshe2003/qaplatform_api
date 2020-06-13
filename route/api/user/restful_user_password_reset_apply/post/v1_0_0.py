# -*- coding: utf-8 -*-

import flask
import re
import datetime
import uuid

from handler.mail import publicmailer
from handler.pool import mysqlpool
from handler.config import appconfig
from handler.log import api_logger
from handler.api.error import ApiError
from handler.api.check import ApiCheck

from model.mysql import model_mysql_useroperationrecord


# 账户申请重置密码-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在，排除不存在的/未激活的/禁用状态的账户
# 3.校验操作码是否有效
# ----操作
# 4.尝试发送包含账户信息确认页url的邮件
# 5.返回信息给前端
def user_password_reset_apply_post():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 1.校验传参
    # 取出请求参数
    try:
        request_json = flask.request.json
    except Exception as e:
        logmsg = "/resetPasswordApply.json数据格式化失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_error("接口数据异常")
    else:
        if request_json is None:
            return ApiError.requestfail_error("接口数据异常")
    # 检查必传参数
    # 1.mail_address
    if "mail_address" not in request_json:
        return ApiError.requestfail_nokey("mail_address")
    # 检查参数合法性
    # 1.mail_address
    if type(request_json["mail_address"]) is not str:
        return ApiError.requestfail_value("mail_address")
    elif re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_json["mail_address"]) is None:
        return ApiError.requestfail_value("mail_address")
    # 检查通过

    # 取出传入参数值
    requestvalue_mail = request_json["mail_address"]

    # 2.校验账户是否存在
    userdata = ApiCheck.check_user(requestvalue_mail)
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

    # 检查通过
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

    # 查库，将之前未进行重置密码操作的记录全部置为无效
    try:
        data = model_mysql_useroperationrecord.query.filter_by(
            userId=userdata["userId"],
            operationId=odata["operationId"],
            recordStatus=0
        ).all()
    except Exception as e:
        logmsg = "mysql中账户操作数据查询失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    for d in data:
        d.recordStatus = -1
    try:
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "mysql中账户操作数据更新失败，失败原因：" + repr(e)
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
    # 将内容入库
    insertdata = model_mysql_useroperationrecord(
        userId=userdata["userId"],
        operationId=odata["operationId"],
        recordCode=code,
        recordStatus=0,
        recordValidTime=(datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    )
    try:
        mysqlpool.session.add(insertdata)
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "mysql中账户操作数据新增失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    # 发送重置密码邮件
    publicmailer.sendmail_reset_password(
        request_json["mail_address"],
        code,
        odata["operationId"]
    )

    # 定义msg
    response_json["error_msg"] = "操作成功，请查收重置密码邮件"
    # 最后返回内容
    return response_json
