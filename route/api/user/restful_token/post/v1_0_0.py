# -*- coding: utf-8 -*-

import flask
import re
import datetime
import uuid

from model.redis import model_redis_usertoken

from handler.log import api_logger
from handler.api.error import ApiError
from handler.api.check import ApiCheck


# 账户手动登陆-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在以及状态是否为正常
# 3.校验账户密码是否正确
# ----操作
# 4.读取账户权限信息，封装基础信息
# 5.将token写入redis
# 6.返回信息
def token_post():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {
            "access_token": {}
        }
    }

    # 1.校验传参
    # 取出请求参数
    try:
        request_json = flask.request.json
    except Exception as e:
        logmsg = "/login.json数据格式化失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_error("接口数据异常")
    else:
        if request_json is None:
            return ApiError.requestfail_error("接口数据异常")
    # 检查必传项是否遗留
    # mail_address
    if "mail_address" not in request_json:
        return ApiError.requestfail_nokey("mail_address")
    # login_password
    elif "login_password" not in request_json:
        return ApiError.requestfail_nokey("login_password")
    # is_checked
    elif "is_checked" not in request_json:
        return ApiError.requestfail_nokey("is_checked")
    # 检查通过
    # 检查必传项内容格式
    # mail_address
    if type(request_json["mail_address"]) is not str or len(request_json["mail_address"]) > 100:
        return ApiError.requestfail_value("mail_address")
    if re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_json["mail_address"]) is None:
        return ApiError.requestfail_value("mail_address")
    # login_password
    if type(request_json["login_password"]) is not str:
        return ApiError.requestfail_value("login_password")
    # is_checked
    if type(request_json["is_checked"]) is not bool:
        return ApiError.requestfail_value("is_checked")
    # 检查通过

    # 取出传入参数值
    requestvalue_mail = request_json["mail_address"]
    requestvalue_password = request_json["login_password"]
    requestvalue_check = request_json["is_checked"]

    # 2.校验账户是否存在以及状态是否为正常
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

    # 3.校验账户密码是否正确
    if requestvalue_password != userdata["userPassword"]:
        return ApiError.requestfail_error("登陆密码错误")

    # 定义data中的user_info
    user_token = str(
        uuid.uuid3(
            uuid.NAMESPACE_DNS, requestvalue_mail + str(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        )
    )
    response_json["data"]["access_token"] = user_token

    # 5.将token写入redis
    if requestvalue_check is True:
        t = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        t = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    model_redis_usertoken.set(
        requestvalue_mail,
        "{\"userToken\":\"" + user_token + "\"," +
        "\"validTime\":\"" + t +
        "\"}"
    )

    # 6.返回信息
    response_json["error_msg"] = "账户登陆成功"
    logmsg = "手动登陆请求处理完毕"
    api_logger.info(logmsg)
    # 最后返回内容
    return response_json
