# -*- coding: utf-8 -*-

import flask
import re
import datetime
import route

from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.mail import publicmailer
from handler.pool import mysqlpool
from handler.log import api_logger

from model.mysql import model_mysql_userinfo, model_mysql_useroperationrecord


# 账户信息补全-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验操作码是否有效
# ----操作
# 4.保存账户头像
# 5.修改账户昵称、登录密码、注册时间、账户状态
# 6.修改操作记录，置为已完成
# 7.发送注册成功邮件
# 8.返回成功信息
@route.check_post_parameter(
    ['file_url', str, 1, None],
    ['user_id', int, 1, None],
    ['mail_address', str, 1, 100],
    ['login_name', str, 1, 100],
    ['record_code', str, 1, 100],
    ['nick_name', str, 1, 100],
    ['operation_id', int, 0, None],
    ['new_password', str, 1, 100],
)
def new_user_info_put():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 取出参数
    rq_file_url = flask.request.json['file_url']
    rq_user_id = flask.request.json['user_id']
    rq_mail_address = flask.request.json['mail_address']
    rq_login_name = flask.request.json['login_name']
    rq_record_code = flask.request.json['record_code']
    rq_nick_name = flask.request.json['nick_name']
    rq_operation_id = flask.request.json['operation_id']
    rq_new_password = flask.request.json['new_password']

    # mail_address
    mail_reg = '^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$'
    if not re.search(mail_reg, rq_mail_address):
        return route.error_msgs[301]['msg_value_type_error']
    # login_name
    name_reg = '^[a-zA-Z][a-z0-9A-Z_]{1,19}$'
    if not re.search(name_reg, rq_login_name):
        return route.error_msgs[301]['msg_value_type_error']

    # 2.校验账户是否存在
    userdata = ApiCheck.check_user(rq_user_id)
    if userdata["exist"] is False:
        return ApiError.requestfail_error("账户不存在")
    elif userdata["exist"] is True and userdata["userStatus"] == 0:
        pass
    elif userdata["exist"] is True and userdata["userStatus"] == 1:
        return ApiError.requestfail_error("账户已激活")
    elif userdata["exist"] is True and userdata["userStatus"] == -1:
        return ApiError.requestfail_error("账户已禁用")
    else:
        return ApiError.requestfail_error("账户信息校验异常")

    # 3.校验操作码是否有效
    codeexist, codevalid = ApiCheck.check_code(userdata["userId"], rq_record_code, rq_operation_id)
    if codeexist is False:
        return ApiError.requestfail_error("操作码错误或不存在")
    elif codeexist is True and codevalid == 0:
        return ApiError.requestfail_error("操作码过期")
    elif codeexist is True and codevalid == 1:
        pass
    else:
        return ApiError.requestfail_server("操作码校验异常")

    # 4.修改账户昵称、登录密码、注册时间、账户状态、头像地址
    # 登录名不可重复
    # 首先判断登录名是否已存在
    try:
        user = model_mysql_userinfo.query.filter_by(
            userLoginName=rq_login_name
        ).first()
    except Exception as e:
        api_logger.error(repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if user is None:
            try:
                user = model_mysql_userinfo.query.filter_by(userId=userdata["userId"]).first()
            except Exception as e:
                logmsg = "/infoConfirm.json账户信息读取失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                return ApiError.requestfail_server(logmsg)
            user.userLoginName = rq_login_name
            user.userNickName = rq_nick_name
            user.userPassword = rq_new_password
            user.userRegisterTime = datetime.datetime.now()
            user.userStatus = 1
            user.userHeadIconUrl = rq_file_url
            # 尝试写入mysql
            try:
                mysqlpool.session.commit()
            # except IntegrityError as e1:
            #     logmsg = "/infoConfirm.json账户信息存入数据库失败，失败原因：" + repr(e)
            #     api_logger.error(logmsg)
            #     return ApiError.requestfail_server(logmsg)
            except Exception as e:
                logmsg = "/infoConfirm.json账户信息存入数据库失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                return ApiError.requestfail_server(logmsg)

            # 6.将操作记录置为已完成
            try:
                record = model_mysql_useroperationrecord.query.filter_by(
                    userId=user.userId,
                    operationId=rq_operation_id,
                    recordStatus=0
                ).first()
            except Exception as e:
                logmsg = "/infoConfirm.json操作记录信息读取失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                return ApiError.requestfail_server(logmsg)
            record.recordStatus = 1
            # 尝试写入mysql
            try:
                mysqlpool.session.commit()
            except Exception as e:
                logmsg = "/infoConfirm.json操作记录信息更新失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                return ApiError.requestfail_server(logmsg)

            # 7.发送注册成功邮件
            send_result_flag, send_result_type = publicmailer.sendmail_register_success(
                rq_mail_address
            )
            # 如果发送失败，则返回错误信息
            if send_result_flag is False:
                if send_result_type == -1:
                    return ApiError.requestfail_server("SMTP服务器连接失败")
                elif send_result_type == 1 or send_result_type == 2:
                    return ApiError.requestfail_server("公共邮箱登陆失败")
                elif send_result_type == 3:
                    return ApiError.requestfail_error("邮件发送失败，请检查邮箱地址")
        else:
            return route.error_msgs[201]['msg_user_exist']

    # 8.返回成功信息
    # 定义msg
    response_json["error_msg"] = "操作成功，请查收账户注册邮件"
    # 最后返回内容
    return response_json
