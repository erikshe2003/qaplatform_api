# -*- coding: utf-8 -*-

import flask
import re
import route

from handler.api.error import ApiError
from handler.api.check import ApiCheck


# 账户令牌校验-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在，排除掉不存在的/已禁用的/未激活的
# 3.校验令牌是否有效
# ----操作
# 4.返回信息
@route.check_get_parameter(
    ['user_token', str, 36, 36]
)
def token_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "",
        "data": {}
    }

    # 取出传入参数值
    requestvalue_userid = int(flask.request.headers["UserId"])

    requestvalue_token = flask.request.args["user_token"]

    # 2.校验账户是否存在
    userdata = ApiCheck.check_user(requestvalue_userid)
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

    # 定义msg
    response_json["msg"] = "token有效"
    # 最后返回内容
    return response_json
