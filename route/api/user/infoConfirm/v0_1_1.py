# -*- coding: utf-8 -*-

import flask
import re
import datetime
import json

from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.sys.saveFile import SaveFile
from handler.mail import publicmailer
from handler.pool import mysqlpool
from handler.log import api_logger

from route.api.user import user_apis

from model.mysql import model_mysql_userinfo, model_mysql_useroperationrecord
from model.redis import model_redis_userinfo


# 账户信息补全-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验操作码是否有效
# ----操作
# 4.保存账户头像
# 5.修改账户昵称、登录密码、注册时间、账户状态
# 6.修改操作记录，置为已完成
# 7.发送注册成功邮件
# 8.返回成功信息
@user_apis.route('/infoConfirm.json', methods=["post"])
def info_confirm():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 1.校验传参
    # 取出请求参数
    try:
        request_form = flask.request.form
        request_file = flask.request.files["file"]
    except Exception as e:
        logmsg = "/infoConfirm.json数据格式化失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_error("接口数据异常")
    # 检查必传项是否遗留
    # mail_address
    if "mail_address" not in request_form:
        return ApiError.requestfail_nokey("mail_address")
    # record_code
    if "record_code" not in request_form:
        return ApiError.requestfail_nokey("record_code")
    # operation_id
    if "operation_id" not in request_form:
        return ApiError.requestfail_nokey("operation_id")
    # new_password
    if "new_password" not in request_form:
        return ApiError.requestfail_nokey("new_password")
    # nick_name
    if "nick_name" not in request_form:
        return ApiError.requestfail_nokey("nick_name")
    # 检查通过
    # 检查必传项内容格式
    # mail_address
    if type(request_form["mail_address"]) is not str or len(request_form["mail_address"]) > 100:
        return ApiError.requestfail_value("mail_address")
    if re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_form["mail_address"]) is None:
        return ApiError.requestfail_value("mail_address")
    # record_code
    if type(request_form["record_code"]) is not str or len(request_form["record_code"]) > 100:
        return ApiError.requestfail_value("record_code")
    # operation_id。此处比较特殊，因为前端传form，value需为str
    if type(request_form["operation_id"]) is not str or len(request_form["operation_id"]) > 100:
        return ApiError.requestfail_value("operation_id")
    # new_password
    if type(request_form["new_password"]) is not str or len(request_form["new_password"]) > 100:
        return ApiError.requestfail_value("new_password")
    # nick_name
    if type(request_form["nick_name"]) is not str or len(request_form["nick_name"]) > 100:
        return ApiError.requestfail_value("nick_name")
    # file
    if "image" in request_file.content_type:
        default = 1
    elif request_file.filename == 'defaultIcon':
        default = 0
    else:
        return ApiError.requestfail_value("file")
    # 由于FileStorage进行read操作后内容会置空，故只能临时处理
    requestvalue_file = request_file.read()
    if len(requestvalue_file) > 500*1024:
        return ApiError.requestfail_value("file")
    # 检查通过

    # 取出传入参数值
    requestvalue_mail = request_form["mail_address"]
    requestvalue_recordcode = request_form["record_code"]
    requestvalue_operationid = request_form["operation_id"]
    requestvalue_newpassword = request_form["new_password"]
    requestvalue_nickname = request_form["nick_name"]
    requestvalue_default = default

    # 2.校验账户是否存在
    userdata = ApiCheck.check_user(requestvalue_mail)
    if userdata["exist"] is False:
        return ApiError.requestfail_error("账户不存在")
    elif userdata["exist"] is True and userdata["userStatus"] == 0:
        pass
    elif userdata["exist"] is True and userdata["userStatus"] == 1:
        return ApiError.requestfail_error("账户已激活")
    elif userdata["exist"] is True and userdata["userStatus"] == -1:
        return ApiError.requestfail_error("账户已禁用")
    else:
        return ApiError.requestfail_error("账户信息校验异常")

    # 3.校验操作码是否有效
    codeexist, codevalid = ApiCheck.check_code(userdata["userId"], requestvalue_recordcode, requestvalue_operationid)
    if codeexist is False:
        return ApiError.requestfail_error("操作码错误或不存在")
    elif codeexist is True and codevalid == 0:
        return ApiError.requestfail_error("操作码过期")
    elif codeexist is True and codevalid == 1:
        pass
    else:
        return ApiError.requestfail_server("操作码校验异常")

    # 4.保存账户头像
    SaveFile.save_icon(requestvalue_file, requestvalue_mail, requestvalue_default)

    # 5.修改账户昵称、登录密码、注册时间、账户状态
    try:
        user = model_mysql_userinfo.query.filter_by(userId=userdata["userId"]).first()
    except Exception as e:
        logmsg = "/infoConfirm.json账户信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    user.userNickName = requestvalue_nickname
    user.userPassword = requestvalue_newpassword
    user.userRegisterTime = datetime.datetime.now()
    user.userStatus = 1
    # 尝试写入mysql
    try:
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "/infoConfirm.json账户信息存入数据库失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    # 尝试写入redis
    try:
        model_redis_userinfo.set(
            requestvalue_mail,
            "{\"userId\":" + str(user.userId) +
            ",\"userNickName\":" + (
                "\"" + str(user.userNickName) + "\"" if user.userNickName is not None else "null"
            ) +
            ",\"userPassword\":" + (
                "\"" + str(user.userPassword) + "\"" if user.userPassword is not None else "null"
            ) +
            ",\"userStatus\":" + str(user.userStatus) +
            ",\"userRoleId\":" + (
                str(user.userRoleId) if user.userRoleId is not None else "null"
            ) + "}"
        )
    except Exception as e:
        logmsg = "/infoConfirm.json账户信息存入缓存失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)

    # 6.将操作记录置为已完成
    try:
        record = model_mysql_useroperationrecord.query.filter_by(
            userId=user.userId,
            operationId=requestvalue_operationid,
            recordStatus=0
        ).first()
    except Exception as e:
        logmsg = "/infoConfirm.json操作记录信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    record.recordStatus = 1
    # 尝试写入mysql
    try:
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "/infoConfirm.json操作记录信息更新失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)

    # 7.发送注册成功邮件
    send_result_flag, send_result_type = publicmailer.sendmail_register_success(
        requestvalue_mail
    )
    # 如果发送失败，则返回错误信息
    if send_result_flag is False:
        if send_result_type == -1:
            return ApiError.requestfail_server("SMTP服务器连接失败")
        elif send_result_type == 1 or send_result_type == 2:
            return ApiError.requestfail_server("公共邮箱登陆失败")
        elif send_result_type == 3:
            return ApiError.requestfail_error("邮件发送失败，请检查邮箱地址")

    # 8.返回成功信息
    # 定义msg
    response_json["error_msg"] = "操作成功，请查收账户注册邮件"
    # 最后返回内容
    return json.dumps(response_json)

