# -*- coding: utf-8 -*-

import flask
import re

from sqlalchemy import and_, func

from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.log import api_logger

from handler.pool import mysqlpool

from model.mysql import model_mysql_userinfo
from model.mysql import model_mysql_useroperationrecord


# 获取账户个人简介-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验账户操作令牌
# ----操作
# 4.返回账户个人简介信息
def user_info_get():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {
            "user_id": '',
            "nick_name": '',
            "mail_address": '',
            "new_mail_address": '',
            "introduction": ''
        }
    }

    # 检查必传项是否遗留
    # mail_address
    if "mail_address" not in flask.request.args:
        return ApiError.requestfail_nokey("mail_address")
    # user_token
    if "user_token" not in flask.request.args:
        return ApiError.requestfail_nokey("user_token")
    # 检查通过
    # 检查必传项内容格式
    # mail_address
    if type(flask.request.args["mail_address"]) is not str or len(flask.request.args["mail_address"]) > 100:
        return ApiError.requestfail_value("mail_address")
    if re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", flask.request.args["mail_address"]) is None:
        return ApiError.requestfail_value("mail_address")
    # record_code
    if type(flask.request.args["user_token"]) is not str or len(flask.request.args["user_token"]) > 100:
        return ApiError.requestfail_value("user_token")

    # 取出传入参数值
    requestvalue_mail = flask.request.args["mail_address"]
    requestvalue_token = flask.request.args["user_token"]

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

    # 4.尝试查询mysql
    # 查询是否有最新的且有效的邮箱变更操作,operateId=3
    try:
        uinfo_mysql = mysqlpool.session.query(
            model_mysql_userinfo.userId,
            model_mysql_userinfo.userNickName,
            model_mysql_userinfo.userEmail,
            model_mysql_userinfo.userNewEmail,
            model_mysql_userinfo.userIntroduction,
            model_mysql_useroperationrecord.recordId
        ).outerjoin(
            model_mysql_useroperationrecord,
            and_(
                model_mysql_userinfo.userId == model_mysql_useroperationrecord.userId,
                model_mysql_useroperationrecord.recordStatus == 0,
                model_mysql_useroperationrecord.operationId == 3,
                model_mysql_useroperationrecord.recordValidTime > func.now()
            )
        ).filter(
            model_mysql_userinfo.userId == userdata["userId"]
        ).first()
    except Exception as e:
        logmsg = "数据库中账户信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        response_json["data"]["user_id"] = uinfo_mysql.userId
        response_json["data"]["nick_name"] = uinfo_mysql.userNickName
        response_json["data"]["mail_address"] = uinfo_mysql.userEmail
        response_json["data"]["new_mail_address"] = uinfo_mysql.userNewEmail if uinfo_mysql.recordId else None
        response_json["data"]["introduction"] = uinfo_mysql.userIntroduction

    # 8.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json

