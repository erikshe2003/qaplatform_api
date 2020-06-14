# -*- coding: utf-8 -*-

import flask
import re
import route

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
@route.check_token
@route.check_user
@route.check_get_parameter(
    ['user_id', int, 1, None]
)
def user_permission_get():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 取出传入参数值
    requestvalue_id = int(flask.request.args["user_id"])

    # 查询
    userdata = ApiCheck.check_user(user_id=requestvalue_id)
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

    # 查询权限信息
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
    return response_json
