# -*- coding: utf-8 -*-

import flask
import re
import datetime
import route

from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.sys.saveFile import SaveFile
from handler.mail import publicmailer
from handler.pool import mysqlpool
from handler.log import api_logger

from model.mysql import model_mysql_userinfo, model_mysql_useroperationrecord


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
def new_user_info_put():
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
        logmsg = "数据格式化失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[301]['msg_value_type_error']
    # 检查必传项是否遗留
    if "user_id" not in request_form:
        return route.error_msgs[302]['msg_request_params_incomplete']
    # mail_address
    if "mail_address" not in request_form:
        return route.error_msgs[302]['msg_request_params_incomplete']
    # record_code
    if "record_code" not in request_form:
        return route.error_msgs[302]['msg_request_params_incomplete']
    # operation_id
    if "operation_id" not in request_form:
        return route.error_msgs[302]['msg_request_params_incomplete']
    # new_password
    if "new_password" not in request_form:
        return route.error_msgs[302]['msg_request_params_incomplete']
    # nick_name
    if "nick_name" not in request_form:
        return route.error_msgs[302]['msg_request_params_incomplete']
    # login_name
    if "login_name" not in request_form:
        return route.error_msgs[302]['msg_request_params_incomplete']
    # 检查通过
    # 检查必传项内容格式
    if type(request_form["user_id"]) is not str or len(request_form["user_id"]) > 100:
        return route.error_msgs[301]['msg_value_type_error']
    # mail_address
    if type(request_form["mail_address"]) is not str or len(request_form["mail_address"]) > 100:
        return route.error_msgs[301]['msg_value_type_error']
    mail_reg = '^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$'
    if not re.search(mail_reg, request_form["mail_address"]):
        return route.error_msgs[301]['msg_value_type_error']
    # record_code
    if type(request_form["record_code"]) is not str or len(request_form["record_code"]) > 100:
        return route.error_msgs[301]['msg_value_type_error']
    # operation_id。此处比较特殊，因为前端传form，value需为str
    if type(request_form["operation_id"]) is not str or len(request_form["operation_id"]) > 100:
        return route.error_msgs[301]['msg_value_type_error']
    # new_password
    if type(request_form["new_password"]) is not str or len(request_form["new_password"]) > 100:
        return route.error_msgs[301]['msg_value_type_error']
    # nick_name
    if type(request_form["nick_name"]) is not str or len(request_form["nick_name"]) > 100:
        return route.error_msgs[301]['msg_value_type_error']
    # login_name
    if type(request_form["login_name"]) is not str or len(request_form["login_name"]) > 20:
        return route.error_msgs[301]['msg_value_type_error']
    name_reg = '^[a-zA-Z][a-z0-9A-Z_]{1,19}$'
    if not re.search(name_reg, request_form["login_name"]):
        return route.error_msgs[301]['msg_value_type_error']
    # file
    if "image" in request_file.content_type:
        default = 1
    elif request_file.filename == 'defaultIcon':
        default = 0
    else:
        return route.error_msgs[301]['msg_value_type_error']
    # 由于FileStorage进行read操作后内容会置空，故只能临时处理
    requestvalue_file = request_file.read()
    if len(requestvalue_file) > 500*1024:
        return route.error_msgs[301]['msg_value_type_error']
    # 检查通过

    # 取出传入参数值
    requestvalue_id = int(request_form["user_id"])
    requestvalue_mail = request_form["mail_address"]
    requestvalue_recordcode = request_form["record_code"]
    requestvalue_operationid = request_form["operation_id"]
    requestvalue_newpassword = request_form["new_password"]
    requestvalue_loginname = request_form["login_name"]
    requestvalue_nickname = request_form["nick_name"]
    requestvalue_default = default

    # 2.校验账户是否存在
    userdata = ApiCheck.check_user(requestvalue_id)
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
    # 登录名不可重复
    # 首先判断登录名是否已存在
    try:
        user = model_mysql_userinfo.query.filter_by(
            userLoginName=requestvalue_loginname
        ).first()
    except Exception as e:
        api_logger.error(repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if user is None:
            try:
                user = model_mysql_userinfo.query.filter_by(userId=userdata["userId"]).first()
            except Exception as e:
                logmsg = "/infoConfirm.json账户信息读取失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                return ApiError.requestfail_server(logmsg)
            user.userLoginName = requestvalue_nickname
            user.userLoginName = requestvalue_loginname
            user.userNickName = requestvalue_nickname
            user.userPassword = requestvalue_newpassword
            user.userRegisterTime = datetime.datetime.now()
            user.userStatus = 1
            # 尝试写入mysql
            try:
                mysqlpool.session.commit()
            # except IntegrityError as e1:
            #     logmsg = "/infoConfirm.json账户信息存入数据库失败，失败原因：" + repr(e)
            #     api_logger.error(logmsg)
            #     return ApiError.requestfail_server(logmsg)
            except Exception as e:
                logmsg = "/infoConfirm.json账户信息存入数据库失败，失败原因：" + repr(e)
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
        else:
            return route.error_msgs[201]['msg_user_exist']

    # 8.返回成功信息
    # 定义msg
    response_json["error_msg"] = "操作成功，请查收账户注册邮件"
    # 最后返回内容
    return response_json
