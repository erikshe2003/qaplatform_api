# -*- coding: utf-8 -*-

import flask
import re
import json

from route.api.user import user_apis

from handler.log import api_logger
from handler.api.error import ApiError
from handler.api.check import ApiCheck


# 账户权限校验-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在，排除掉不存在的/已禁用的/未激活的
# 3.校验令牌是否有效
# ----操作
# 4.于redis中查询并返回permission配置信息
# 5.若redis中无，则去mysql中查询，然后写入redis
@user_apis.route('/checkPermission.json', methods=["post"])
def check_permission():
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
        logmsg = "/checkToken.json数据格式化失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_error("接口数据异常")
    else:
        if request_json is None:
            return ApiError.requestfail_error("接口数据异常")
    # 检查必传项是否遗留
    # mail_address
    if "mail_address" not in request_json:
        return ApiError.requestfail_nokey("mail_address")
    # user_token
    if "user_token" not in request_json:
        return ApiError.requestfail_nokey("user_token")
    # 检查通过
    # 检查必传项内容格式
    # mail_address
    if type(request_json["mail_address"]) is not str or len(request_json["mail_address"]) > 100:
        return ApiError.requestfail_value("mail_address")
    if re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_json["mail_address"]) is None:
        return ApiError.requestfail_value("mail_address")
    # record_code
    if type(request_json["user_token"]) is not str or len(request_json["user_token"]) > 100:
        return ApiError.requestfail_value("user_token")

    # 取出传入参数值
    requestvalue_mail = request_json["mail_address"]
    requestvalue_token = request_json["user_token"]

    # 2.校验账户是否存在
    userdata = ApiCheck.check_user(requestvalue_mail)
    if userdata["exist"] is False:
        return ApiError.requestfail_error("账户不存在")
    elif userdata["exist"] is True and userdata["userStatus"] == 0:
        return ApiError.requestfail_error("账户未激活")
    elif userdata["exist"] is True and userdata["userStatus"] == 1:
        pass
    elif userdata["exist"] is True and userdata["userStatus"] == -1:
        return ApiError.requestfail_error("账户已禁用")
    else:
        return ApiError.requestfail_error("账户信息校验异常")

    # 3.校验令牌是否有效
    tc = ApiCheck.check_token(
        requestvalue_mail,
        requestvalue_token
    )
    if tc["exist"] is True and tc["valid"] is True:
        pass
    elif tc["exist"] is True and tc["valid"] is False:
        return ApiError.requestfail_error("token已过期")
    elif tc["exist"] is False:
        return ApiError.requestfail_error("token错误")
    else:
        return ApiError.requestfail_server("token校验失败")

    # 4.校验权限信息
    rp = ApiCheck.check_role_permission(
        userdata['userRoleId']
    )
    if rp["exist"] is True:
        response_json["data"]["permission"] = rp["rolePermission"]
    elif rp["exist"] is False:
        response_json["data"]["permission"] = {}
    else:
        return ApiError.requestfail_server("角色权限信息处理异常")

    # 定义msg
    response_json["error_msg"] = "token有效"
    # 最后返回内容
    return json.dumps(response_json)
