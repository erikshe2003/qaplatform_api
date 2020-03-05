# -*- coding: utf-8 -*-

import flask
import json
import route

from handler.pool import mysqlpool
from handler.log import api_logger, db_logger
from handler.api.error import ApiError

from route.api.user import user_apis

from model.mysql import model_mysql_userinfo

from model.redis import model_redis_userinfo


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


@user_apis.route('/modifyPassword.json', methods=["post"])
@route.check_token
@route.check_user
# @route.check_auth
@route.check_post_parameter(
    ['oldPassword', str, 1, 100],
    ['newPassword', str, 1, 100],
    ['confirmPassword', str, 1, 100]
)
def modify_password():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {}
    }

    # 取出参数
    mail_address = flask.request.headers['Mail']
    old_password = flask.request.json['oldPassword']
    new_password = flask.request.json['newPassword']
    confirm_password = flask.request.json['confirmPassword']

    # 判断新密码与确认密码是否一致
    if new_password != confirm_password:
        return route.error_msgs['msg_new_password_inconformity']

    # 根据mail_address在缓存中查找账户id以及旧密码
    redis_user_info = model_redis_userinfo.query(user_email=mail_address)
    # 如果缓存中没查到，则查询mysql
    if redis_user_info is None:
        try:
            mysql_user_info = model_mysql_userinfo.query.filter(
                model_mysql_userinfo.userEmail == mail_address
            ).first()
            db_logger.debug(mail_address + "的账户基础信息读取成功")
        except Exception as e:
            db_logger.error(mail_address + "的账户基础信息读取失败，失败原因：" + repr(e))
            return route.error_msgs['msg_db_error']
        else:
            if mysql_user_info is None:
                return route.error_msgs['msg_no_user']
            else:
                user_id = mysql_user_info.userId
                user_pass = mysql_user_info.userPassword
    else:
        # 格式化缓存中基础信息内容
        try:
            redis_user_info_json = json.loads(redis_user_info.decode("utf8"))
            db_logger.debug(mail_address + "的缓存账户数据json格式化成功")
        except Exception as e:
            db_logger.error(mail_address + "的缓存账户数据json格式化失败，失败原因：" + repr(e))
            return route.error_msgs['msg_json_format_fail']
        else:
            user_id = redis_user_info_json['userId']
            user_pass = redis_user_info_json['userPassword']

    # 根据userId查询旧密码，并判断一致性
    if user_pass != old_password:
        return route.error_msgs['msg_old_password_incorrect']
    else:
        # 更新mysql密码
        mysql_new_user_info = model_mysql_userinfo.query.filter(
            model_mysql_userinfo.userId == user_id
        ).first()
        mysql_new_user_info.userPassword = new_password
        try:
            mysqlpool.session.commit()
        except Exception as e:
            db_logger.error(mail_address + "的账户基础信息更新失败，失败原因：" + repr(e))
            return route.error_msgs['msg_db_error']
        # 更新redis密码
        try:
            model_redis_userinfo.set(
                mail_address,
                "{\"userId\":%d, "
                "\"userNickName\":\"%s\", "
                "\"userPassword\":\"%s\", "
                "\"userStatus\":%d, "
                "\"userRoleId\":%s}" % (
                    mysql_new_user_info.userId,
                    mysql_new_user_info.userNickName if mysql_new_user_info.userNickName is not None else "null",
                    mysql_new_user_info.userPassword if mysql_new_user_info.userPassword is not None else "null",
                    mysql_new_user_info.userStatus,
                    mysql_new_user_info.userRoleId if mysql_new_user_info.userRoleId is not None else "null"
                )
            )
        except Exception as e:
            logmsg = "redis中账户信息更新失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return ApiError.requestfail_server(logmsg)

    # 最后返回内容
    return json.dumps(response_json)
