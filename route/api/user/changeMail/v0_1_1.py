# -*- coding: utf-8 -*-

import flask
import json
import re

from handler.mail import publicmailer
from handler.log import api_logger
from handler.pool import mysqlpool
from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.sys.saveFile import SaveFile

from route.api.user import user_apis

from model.mysql import model_mysql_useroperationrecord, model_mysql_userinfo
from model.redis import model_redis_userinfo, model_redis_usertoken


# 账户重置密码-api路由
# ----校验
# 1.校验传参
# 2.校验账户状态
# 3.校验操作类型和操作码
# 4.校验账户登录密码
# 5.校验所修改邮箱地址是否已被人绑定
# 6.校验所修改邮箱地址是否正确
# ----操作
# 7.清空旧邮箱在redis中的账户基本信息
# 8.修改所旧邮箱为新邮箱，然后清空新邮箱记录
# 9.刷新旧邮箱密码
# 10.将账户旧文件夹名称修改为新文件夹名称
# 11.将修改绑定邮箱的记录修改为已完成
# 12.发送修改绑定邮箱成功邮件
@user_apis.route('/changeMail.json', methods=["post"])
def change_mail():
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
        logmsg = "/changeMail.json数据格式化失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_error("接口数据异常")
    else:
        if request_json is None:
            return ApiError.requestfail_error("接口数据异常")
    # 检查必传项是否遗留
    # mail_address
    if "mail_address" not in request_json:
        return ApiError.requestfail_nokey("mail_address")
    # new_mail_address
    if "new_mail_address" not in request_json:
        return ApiError.requestfail_nokey("new_mail_address")
    # record_code
    if "record_code" not in request_json:
        return ApiError.requestfail_nokey("record_code")
    # operation_id
    if "operation_id" not in request_json:
        return ApiError.requestfail_nokey("operation_id")
    # password
    if "password" not in request_json:
        return ApiError.requestfail_nokey("password")
    # password
    if "new_password" not in request_json:
        return ApiError.requestfail_nokey("new_password")
    # 检查通过
    # 检查必传项内容格式
    # mail_address
    if type(request_json["mail_address"]) is not str or len(request_json["mail_address"]) > 100:
        return ApiError.requestfail_value("mail_address")
    elif re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_json["mail_address"]) is None:
        return ApiError.requestfail_value("mail_address")
    # new_mail_address
    if type(request_json["new_mail_address"]) is not str or len(request_json["new_mail_address"]) > 100:
        return ApiError.requestfail_value("new_mail_address")
    elif re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_json["new_mail_address"]) is None:
        return ApiError.requestfail_value("new_mail_address")
    # record_code
    if type(request_json["record_code"]) is not str or len(request_json["record_code"]) > 100:
        return ApiError.requestfail_value("record_code")
    # operation_id
    if type(request_json["operation_id"]) is not int:
        return ApiError.requestfail_value("operation_id")
    # password
    if type(request_json["password"]) is not str or len(request_json["password"]) > 100:
        return ApiError.requestfail_value("password")
    # new_password
    if type(request_json["new_password"]) is not str or len(request_json["new_password"]) > 100:
        return ApiError.requestfail_value("new_password")

    # 校验通过后赋值
    requestvalue_mail = request_json["mail_address"]
    requestvalue_newmail = request_json["new_mail_address"]
    requestvalue_recordcode = request_json["record_code"]
    requestvalue_operationid = request_json["operation_id"]
    requestvalue_password = request_json["password"]
    requestvalue_newpassword = request_json["new_password"]

    # 2.校验账户状态
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

    # 3.校验操作类型和操作码
    codeexist, codevalid = ApiCheck.check_code(userdata["userId"], requestvalue_recordcode, requestvalue_operationid)
    if codeexist is False:
        return ApiError.requestfail_error("操作码错误或不存在")
    elif codeexist is True and codevalid == 0:
        return ApiError.requestfail_error("操作码过期")
    elif codeexist is True and codevalid == 1:
        pass
    else:
        return ApiError.requestfail_server("操作码校验异常")

    # 4.校验账户登录密码
    if userdata["userPassword"] == requestvalue_password:
        pass
    else:
        return ApiError.requestfail_error("密码错误")

    # 5.校验所修改邮箱地址是否已被人绑定
    newuserdata = ApiCheck.check_user(requestvalue_newmail)
    if newuserdata["exist"] is False:
        pass
    else:
        return ApiError.requestfail_error("新邮箱地址已被绑定")

    # 6.校验所修改邮箱地址是否正确
    try:
        uinfo_mysql = model_mysql_userinfo.query.filter_by(userId=userdata["userId"]).first()
    except Exception as e:
        logmsg = "mysql中账户信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    if uinfo_mysql.userNewEmail == requestvalue_newmail:
        pass
    else:
        return ApiError.requestfail_error("新邮箱地址错误")

    # 7.清空旧邮箱在redis中的账户基本信息
    try:
        model_redis_userinfo.delete(requestvalue_mail)
        model_redis_usertoken.delete(requestvalue_mail)
    except Exception as e:
        logmsg = "redis中账户缓存数据删除失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)

    # 8.修改所旧邮箱为新邮箱，然后清空新邮箱记录
    uinfo_mysql.userEmail = requestvalue_newmail
    uinfo_mysql.userNewEmail = None
    try:
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "mysql中账户邮箱绑定数据更新失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)

    # 9.修改账号密码
    uinfo_mysql.userPassword = requestvalue_newpassword
    try:
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "mysql中账户信息更新失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)

    # 10.将账户旧文件夹名称修改为新文件夹名称
    SaveFile.move_dir(
        requestvalue_mail,
        requestvalue_newmail
    )

    # 11.将修改绑定邮箱的记录修改为已完成
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

    # 12.发送修改绑定邮箱成功邮件
    publicmailer.sendmail_changemail_success(
        requestvalue_newmail
    )
    # 定义msg
    response_json["error_msg"] = "操作成功，请到新邮箱中查收修改成功邮件"
    # 最后返回内容
    return json.dumps(response_json)
