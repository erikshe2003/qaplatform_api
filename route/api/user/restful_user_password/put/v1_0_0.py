# -*- coding: utf-8 -*-

import flask
import route

from handler.pool import mysqlpool
from handler.log import api_logger, db_logger
from handler.api.error import ApiError

from model.mysql import model_mysql_userinfo


"""
    修改账户登录密码-api路由
    ----校验
            校验token
            校验user
            校验auth
    ----操作
            判断旧密码是否正确
            判断新密码与确认密码是否一致
            修改密码
"""


@route.check_token
@route.check_user
# @route.check_auth
@route.check_post_parameter(
    ['oldPassword', str, 1, 100],
    ['newPassword', str, 1, 100],
    ['confirmPassword', str, 1, 100]
)
def user_password_put():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "操作成功",
        "data": {}
    }

    # 取出参数
    user_id = flask.request.headers['UserId']
    old_password = flask.request.json['oldPassword']
    new_password = flask.request.json['newPassword']
    confirm_password = flask.request.json['confirmPassword']

    # 判断新密码与确认密码是否一致
    if new_password != confirm_password:
        return route.error_msgs[201]['msg_new_password_inconformity']

    # 查找账户id以及旧密码
    try:
        mysql_user_info = model_mysql_userinfo.query.filter(
            model_mysql_userinfo.userId == user_id
        ).first()
        db_logger.debug("账户基础信息读取成功")
    except Exception as e:
        db_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_user_info is None:
            return route.error_msgs[201]['msg_no_user']
        else:
            user_pass = mysql_user_info.userPassword

    # 根据userId查询旧密码，并判断一致性
    if user_pass != old_password:
        return route.error_msgs[201]['msg_old_password_incorrect']
    else:
        # 更新mysql密码
        mysql_user_info.userPassword = new_password
        try:
            mysqlpool.session.commit()
            db_logger.debug("账户基础信息修改成功")
        except Exception as e:
            db_logger.error("账户基础信息更新失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']

    # 最后返回内容
    return response_json
