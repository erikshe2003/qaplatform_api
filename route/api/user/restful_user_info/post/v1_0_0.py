# -*- coding: utf-8 -*-

import flask
import re
import datetime
import uuid

from handler.mail import publicmailer
from handler.pool import mysqlpool
from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.config import appconfig
from handler.log import api_logger

from model.mysql import model_mysql_useroperationrecord
from model.mysql import model_mysql_userinfo
from model.redis import model_redis_userinfo


# 申请新增账户-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在，排除存在的且为正常的账户/禁用状态的账户
# ----操作
# 3.如果账户不存在，则数据库以及缓存中插入未激活状态的账户数据以及对应的未完成的操作记录
# 4.如果账户存在但状态为未激活，则将先前的账户操作记录数据置为无效，然后插入新的未完成的操作记录
# 5.尝试发送包含账户信息确认页url的邮件
# 6.返回信息给前端
def user_info_post():
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
        logmsg = "/registerApply.json数据格式化失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_error("接口数据异常")
    else:
        if request_json is None:
            return ApiError.requestfail_error("接口数据异常")
    # 检查必传项是否遗留
    # mail_address
    if "mail_address" not in request_json:
        return ApiError.requestfail_nokey("mail_address")
    # 检查通过
    # 检查必传项内容格式
    # mail_address
    if type(request_json["mail_address"]) is not str or len(request_json["mail_address"]) > 100:
        return ApiError.requestfail_value("mail_address")
    elif re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_json["mail_address"]) is None:
        return ApiError.requestfail_value("mail_address")
    # 检查通过

    # 取出传入参数值
    requestvalue_mail = request_json["mail_address"]

    # 2.校验账户是否存在
    userdata = ApiCheck.check_user(requestvalue_mail)
    if userdata["exist"] is False:
        pass
    elif userdata["exist"] is True and userdata["userStatus"] == 0:
        pass
    elif userdata["exist"] is True and userdata["userStatus"] in [-2, -1, 1]:
        return ApiError.requestfail_error("该邮箱已被注册")
    else:
        return ApiError.requestfail_error("账户信息校验异常")

    # 3.如果账户不存在，则数据库以及缓存中插入未激活状态的账户数据以及对应的未完成的操作记录
    if userdata["exist"] is False:
        # 查询关键操作唯一标识符
        odata = ApiCheck.check_operate(
            appconfig.get("operation_alias", "register")
        )
        if odata["exist"] is True:
            pass
        elif odata["exist"] is False:
            return ApiError.requestfail_error("关键操作别名不存在")
        else:
            return ApiError.requestfail_server("操作处理异常")

        # 生成操作码
        code = str(
            uuid.uuid3(
                uuid.NAMESPACE_DNS, requestvalue_mail + str(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
        )
        # 发送包含账户信息确认页链接的邮件
        # 先发送邮件，成功后再记录数据
        # 保证过滤掉不存在的邮件地址
        send_result_flag, send_result_type = publicmailer.sendmail_register(
            requestvalue_mail,
            code,
            odata["operationId"]
        )
        # 如果发送失败，则返回错误信息
        if send_result_flag is False:
            if send_result_type == -1:
                return ApiError.requestfail_server("SMTP服务器连接失败")
            elif send_result_type == 1 or send_result_type == 2:
                return ApiError.requestfail_server("公共邮箱登陆失败")
            elif send_result_type == 3:
                return ApiError.requestfail_error("邮件发送失败，请检查邮箱地址")
        # 在库中插入账户未激活的信息
        # 先插入mysql
        newuser = model_mysql_userinfo(
            userEmail=requestvalue_mail,
            userStatus=0,
            userAddTime=datetime.datetime.now()
        )
        try:
            mysqlpool.session.add(newuser)
            mysqlpool.session.commit()
        except Exception as e:
            logmsg = "数据库新增账户数据失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return ApiError.requestfail_server(logmsg)
        # 然后写入redis
        try:
            model_redis_userinfo.set(
                str(requestvalue_mail),
                "{\"userId\":" + str(newuser.userId) +
                ",\"userNickName\":null" +
                ",\"userPassword\":null" +
                ",\"userStatus\":0" +
                ",\"userRoleId\":null}"
            )
        except Exception as e:
            logmsg = "缓存新增账户数据失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return ApiError.requestfail_server(logmsg)
        # 将操作码数据写入mysql
        insertdata = model_mysql_useroperationrecord(
            userId=newuser.userId,
            operationId=odata["operationId"],
            recordCode=code,
            recordStatus=0,
            recordValidTime=(datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        )
        try:
            mysqlpool.session.add(insertdata)
            mysqlpool.session.commit()
        except Exception as e:
            logmsg = "数据库新增申请账户记录数据失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return ApiError.requestfail_server(logmsg)
    # 4.如果账户存在但状态为未激活，则将先前的账户操作记录数据置为无效，然后插入新的未完成的操作记录
    elif userdata["exist"] is True and userdata["userStatus"] == 0:
        # 查询关键操作唯一标识符
        odata = ApiCheck.check_operate(
            appconfig.get("operation_alias", "register")
        )
        if odata["exist"] is True:
            pass
        elif odata["exist"] is False:
            return ApiError.requestfail_error("关键操作别名不存在")
        else:
            return ApiError.requestfail_server("操作处理异常")

        # 生成操作码
        code = str(
            uuid.uuid3(
                uuid.NAMESPACE_DNS, requestvalue_mail + str(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
        )
        # 发送包含账户信息确认页链接的邮件
        send_result_flag, send_result_type = publicmailer.sendmail_register(
            requestvalue_mail,
            code,
            odata["operationId"]
        )
        # 如果发送失败，则返回错误信息
        if send_result_flag is False:
            if send_result_type == -1:
                return ApiError.requestfail_server("SMTP服务器连接失败")
            elif send_result_type == 1 or send_result_type == 2:
                return ApiError.requestfail_server("公共邮箱登陆失败")
            elif send_result_type == 3:
                return ApiError.requestfail_error("邮件发送失败，请检查邮箱地址")
        # 查询mysql中的操作记录
        try:
            rdata_mysql = model_mysql_useroperationrecord.query.filter_by(
                userId=userdata["userId"],
                operationId=odata["operationId"],
                recordStatus=0
            ).all()
        except Exception as e:
            logmsg = "账户操作记录数据查询失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return ApiError.requestfail_server(logmsg)
        # 如果查询到了，则全部置为无效
        if rdata_mysql is not None:
            for d in rdata_mysql:
                d.recordStatus = -1
            try:
                mysqlpool.session.commit()
            except Exception as e:
                logmsg = "账户操作记录数据更新失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                return ApiError.requestfail_server(logmsg)
        # 将新操作码数据写入mysql
        insertdata = model_mysql_useroperationrecord(
            userId=userdata["userId"],
            operationId=odata["operationId"],
            recordCode=code,
            recordStatus=0,
            recordValidTime=(datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        )
        try:
            mysqlpool.session.add(insertdata)
            mysqlpool.session.commit()
        except Exception as e:
            logmsg = "账户操作记录数据新增失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return ApiError.requestfail_server(logmsg)
    # 5.如果账户存在且状态不为未激活，则将告知前端账户已存在
    else:
        return ApiError.requestfail_error("账户已存在")
    # 定义msg
    response_json["error_msg"] = "操作成功，请查收账户注册邮件"
    # 最后返回内容
    return response_json
