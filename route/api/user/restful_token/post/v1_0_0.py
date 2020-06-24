# -*- coding: utf-8 -*-

import flask
import datetime
import uuid
import route

from model.mysql import model_mysql_userinfo

from model.redis import model_redis_usertoken

from handler.log import api_logger
from handler.api.error import ApiError


# 账户手动登陆-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在以及状态是否为正常
# 3.校验账户密码是否正确
# ----操作
# 4.读取账户权限信息，封装基础信息
# 5.将token写入redis
# 6.返回信息
@route.check_post_parameter(
    ['login_name', str, 1, None],
    ['login_password', str, 1, None],
    ['is_checked', bool]
)
def token_post():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {
            "user_id": 0,
            "access_token": ''
        }
    }

    # 取出传入参数值
    requestvalue_name = flask.request.json["login_name"]
    requestvalue_password = flask.request.json["login_password"]
    requestvalue_check = flask.request.json["is_checked"]

    # 尝试从mysql中查询
    try:
        uinfo_mysql = model_mysql_userinfo.query.filter_by(
            userLoginName=requestvalue_name
        ).first()
    except:
        return route.error_msgs[500]['msg_db_error']
    else:
        if uinfo_mysql is None:
            return route.error_msgs[201]['msg_no_user']
        elif uinfo_mysql.userStatus == 1:
            pass
        elif uinfo_mysql.userStatus == 0:
            return route.error_msgs[201]['msg_need_register']
        elif uinfo_mysql.userStatus == -1:
            return route.error_msgs[201]['msg_user_forbidden']
        else:
            return route.error_msgs[201]['msg_status_error']

    # 3.校验账户密码是否正确
    if requestvalue_password != uinfo_mysql.userPassword:
        return ApiError.requestfail_error("登陆密码错误")

    # 刷新token
    response_json["data"]["access_token"] = route.refresh_redis_usertoken(uinfo_mysql.userId, requestvalue_check)

    response_json["data"]["user_id"] = uinfo_mysql.userId

    # 6.返回信息
    response_json["error_msg"] = "账户登陆成功"
    logmsg = "手动登陆请求处理完毕"
    api_logger.info(logmsg)
    # 最后返回内容
    return response_json
