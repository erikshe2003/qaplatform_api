# -*- coding: utf-8 -*-

import flask
import re
import datetime
import uuid

from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.sys.saveFile import SaveFile
from handler.mail import publicmailer
from handler.pool import mysqlpool
from handler.log import api_logger
from handler.config import appconfig

from model.mysql import model_mysql_userinfo, model_mysql_useroperationrecord
from model.redis import model_redis_userinfo


# 基础信息修改-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验新账户是否存在，排除存在的场景
# ----操作
# 4.如果邮箱账户未变化，则不发送更改邮箱地址的邮件，不进行此操作
# 5.如果账户不存在，则提前生成操作码，尝试发送修改邮箱确认邮件。
# 如果邮件发送成功，修改操作记录，将之前的修改绑定邮箱的操作记录
# 置为-1，并在账号表中新增/覆盖userNewEmail字段内容
# 6.保存账户头像
# 7.修改账户昵称/个人简介
# 9.返回成功信息
def user_info_put():
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
        logmsg = "/setBaseInfo.json数据格式化失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_error("接口数据异常")
    # 检查必传项是否遗留
    # mail_address
    if "mail_address" not in request_form:
        return ApiError.requestfail_nokey("mail_address")
    # new_mail_address
    if "new_mail_address" not in request_form:
        return ApiError.requestfail_nokey("new_mail_address")
    # nick_name
    if "nick_name" not in request_form:
        return ApiError.requestfail_nokey("nick_name")
    # introduce_content
    if "introduce_content" not in request_form:
        return ApiError.requestfail_nokey("introduce_content")
    # user_token
    if "user_token" not in request_form:
        return ApiError.requestfail_nokey("user_token")
    # 检查通过
    # 检查必传项内容格式
    # mail_address
    if type(request_form["mail_address"]) is not str or len(request_form["mail_address"]) > 100:
        return ApiError.requestfail_value("mail_address")
    if re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_form["mail_address"]) is None:
        return ApiError.requestfail_value("mail_address")
    # new_mail_address
    if type(request_form["new_mail_address"]) is not str or len(request_form["new_mail_address"]) > 100:
        return ApiError.requestfail_value("new_mail_address")
    if re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_form["new_mail_address"]) is None:
        return ApiError.requestfail_value("new_mail_address")
    # nick_name
    if type(request_form["nick_name"]) is not str or len(request_form["nick_name"]) > 100:
        return ApiError.requestfail_value("nick_name")
    # introduce_content
    if type(request_form["introduce_content"]) is not str or len(request_form["introduce_content"]) > 200:
        return ApiError.requestfail_value("introduce_content")
    # file
    if "image" in request_file.content_type:
        default = 1
    elif request_file.filename == 'defaultIcon':
        default = 0
    elif request_file.filename == 'userDefaultIcon':
        default = 2
    else:
        return ApiError.requestfail_value("file")
    # 由于FileStorage进行read操作后内容会置空，故只能临时处理
    requestvalue_file = request_file.read()
    if len(requestvalue_file) > 500*1024:
        return ApiError.requestfail_value("file")
    # 检查通过

    # 取出传入参数值
    requestvalue_mail = request_form["mail_address"]
    requestvalue_newmail = request_form["new_mail_address"]
    requestvalue_nickname = request_form["nick_name"]
    requestvalue_introduction = request_form["introduce_content"]
    requestvalue_default = default

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

    if requestvalue_mail == requestvalue_newmail:
        # 定义msg
        response_json["error_msg"] = "基础信息修改成功"
    else:
        # 3.校验新账户是否存在，排除存在的场景
        newuserdata = ApiCheck.check_user(requestvalue_newmail)
        if newuserdata["exist"] is False:
            pass
        elif newuserdata["exist"] is True:
            return ApiError.requestfail_error("新绑定邮箱已被注册")
        else:
            return ApiError.requestfail_error("新绑定邮箱信息校验异常")

        # 4.如果邮箱账户未变化，则不发送更改邮箱地址的邮件，不进行此操作

        # 5.如果账户不存在，则提前生成操作码，尝试发送修改邮箱确认邮件。如果邮件发送
        # 成功，则在账号表中新增/覆盖userNewEmail字段内容
        # 查询关键操作唯一标识符
        odata = ApiCheck.check_operate(
            appconfig.get("operation_alias", "changeMail")
        )
        if odata["exist"] is True:
            pass
        elif odata["exist"] is False:
            return ApiError.requestfail_error("关键操作别名不存在")
        else:
            return ApiError.requestfail_server("操作处理异常")
        if newuserdata["exist"] is False:
            # 提前生成操作码
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
            send_result_flag, send_result_type = publicmailer.sendmail_change_mail(
                requestvalue_mail,
                requestvalue_newmail,
                code,
                3
            )
            # 如果发送失败，则返回错误信息
            if send_result_flag is False:
                if send_result_type == -1:
                    return ApiError.requestfail_server("SMTP服务器连接失败")
                elif send_result_type == 1 or send_result_type == 2:
                    return ApiError.requestfail_server("公共邮箱登陆失败")
                elif send_result_type == 3:
                    return ApiError.requestfail_error("邮件发送失败，请检查邮箱地址")
            # 在库中获取账户信息，准备修改新邮箱信息
            try:
                user = model_mysql_userinfo.query.filter_by(
                    userId=userdata["userId"]
                ).first()
            except Exception as e:
                logmsg = "数据库账户数据查询失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                return ApiError.requestfail_server(logmsg)
            else:
                # 修改其新邮件地址信息
                user.userNewEmail = requestvalue_newmail
                # 然后更新
                try:
                    mysqlpool.session.commit()
                except Exception as e:
                    logmsg = "mysql中账户操作记录更新失败，失败原因：" + repr(e)
                    api_logger.error(logmsg)
                    return ApiError.requestfail_server(logmsg)
                # 8.修改操作记录，将之前的修改绑定邮箱的操作记录置为-1
                try:
                    rdata_mysql = model_mysql_useroperationrecord.query.filter_by(
                        userId=userdata["userId"],
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
            # 将操作码数据写入mysql
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
                logmsg = "数据库新增申请修改绑定邮箱记录数据失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                return ApiError.requestfail_server(logmsg)
        response_json["error_msg"] = "基础信息修改成功，请于新邮箱查收修改绑定邮箱确认邮件"

    # 6.保存账户头像
    if requestvalue_default == 2:
        pass
    else:
        SaveFile.save_icon(requestvalue_file, requestvalue_mail, requestvalue_default)

    # 7.修改账户昵称/个人简介
    try:
        user = model_mysql_userinfo.query.filter_by(userId=userdata["userId"]).first()
    except Exception as e:
        logmsg = "/setBaseInfo.json账户信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    user.userNickName = requestvalue_nickname
    user.userIntroduction = requestvalue_introduction
    # 尝试写入mysql
    try:
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "/setBaseInfo.json账户信息存入数据库失败，失败原因：" + repr(e)
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
        logmsg = "/setBaseInfo.json账户信息存入缓存失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)

    # 8.返回成功信息
    # 最后返回内容
    return response_json
