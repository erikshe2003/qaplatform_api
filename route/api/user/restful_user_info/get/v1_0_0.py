# -*- coding: utf-8 -*-

import flask
import re
import route

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
@route.check_token
@route.check_user
@route.check_get_parameter(
    ['user_id', int, 1, None]
)
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

    # 取出传入参数值
    requestvalue_id = flask.request.args["user_id"]

    # 尝试查询mysql
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
            model_mysql_userinfo.userId == requestvalue_id
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

