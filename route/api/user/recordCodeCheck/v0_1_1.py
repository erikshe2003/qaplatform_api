# -*- coding: utf-8 -*-

import flask
import json
import re

from route.api.user import user_apis

from handler.log import api_logger
from handler.api.check import ApiCheck
from handler.api.error import ApiError


# 账户重置密码-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验操作码是否有效
# ----操作
# 4.返回校验数据
@user_apis.route('/recordCodeCheck.json', methods=["post"])
def record_code_check():
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
        logmsg = "/recordCodeCheck.json数据格式化失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_error("接口数据异常")
    else:
        if request_json is None:
            return ApiError.requestfail_error("接口数据异常")
    # 检查必传项是否遗留
    # 1.mail_address
    if "mail_address" not in request_json:
        return ApiError.requestfail_nokey("mail_address")
    # 2.record_code
    if "record_code" not in request_json:
        return ApiError.requestfail_nokey("record_code")
    # 3.operation_id
    if "operation_id" not in request_json:
        return ApiError.requestfail_nokey("operation_id")
    # 检查通过
    # 检查必传项内容格式
    # 1.mail_address
    if type(request_json["mail_address"]) is not str or len(request_json["mail_address"]) > 100:
        return ApiError.requestfail_value("mail_address")
    elif re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_json["mail_address"]) is None:
        return ApiError.requestfail_value("mail_address")
    # 2.record_code
    if type(request_json["record_code"]) is not str or len(request_json["record_code"]) > 100:
        return ApiError.requestfail_value("record_code")
    # 3.operation_id
    if type(request_json["operation_id"]) is not int:
        return ApiError.requestfail_value("operation_id")
    # 检查通过

    # 取出传入参数值
    requestvalue_mail = request_json["mail_address"]
    requestvalue_recordcode = request_json["record_code"]
    requestvalue_operateid = request_json["operation_id"]

    # 2.校验账户是否存在
    userdata = ApiCheck.check_user(requestvalue_mail)
    if userdata["exist"] is False:
        return ApiError.requestfail_error("账户不存在")
    elif userdata["exist"] is True and userdata["userStatus"] in [0, 1]:
        pass
    elif userdata["userStatus"] == -1:
        return ApiError.requestfail_error("账户已禁用")
    else:
        return ApiError.requestfail_error("账户信息校验异常")

    # 3.校验操作码是否有效
    codeexist, codevalid = ApiCheck.check_code(userdata["userId"], requestvalue_recordcode, requestvalue_operateid)
    if codeexist is False:
        return ApiError.requestfail_error("操作码错误或不存在")
    elif codeexist is True and codevalid == 0:
        return ApiError.requestfail_error("操作码过期")
    elif codeexist is True and codevalid == 1:
        pass
    else:
        return ApiError.requestfail_server("操作码校验异常")

    # 4.返回校验数据
    response_json["error_msg"] = "账户操作码校验通过"
    # 最后返回内容
    return json.dumps(response_json)
