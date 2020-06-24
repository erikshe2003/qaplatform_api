# -*- coding: utf-8 -*-

import flask
import re
import datetime
import uuid
import route

from sqlalchemy import or_

from handler.mail import publicmailer
from handler.pool import mysqlpool
from handler.config import appconfig
from handler.log import api_logger
from handler.api.error import ApiError
from handler.api.check import ApiCheck

from model.mysql import model_mysql_useroperationrecord
from model.mysql import model_mysql_userinfo


# 账户申请重置密码-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在，排除不存在的/未激活的/禁用状态的账户
# 3.校验操作码是否有效
# ----操作
# 4.尝试发送包含账户信息确认页url的邮件
# 5.返回信息给前端
@route.check_post_parameter(
    ['mail_address', str, 1, None]
)
def user_password_reset_apply_post():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 取出传入参数值
    requestvalue_mail = flask.request.json["mail_address"]

    # 校验邮箱地址格式
    mail_reg = '^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$'
    if not re.search(mail_reg, requestvalue_mail):
        return route.error_msgs[201]['msg_illegal_format']

    # 2.校验账户是否存在
    try:
        uinfo_mysql = model_mysql_userinfo.query.filter(
            or_(
                model_mysql_userinfo.userEmail == requestvalue_mail,
                model_mysql_userinfo.userNewEmail == requestvalue_mail
            )
        ).first()
    except Exception as e:
        logmsg = "数据库中账户信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
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

    # 检查通过
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

    # 查库，将之前未进行重置密码操作的记录全部置为无效
    try:
        data = model_mysql_useroperationrecord.query.filter_by(
            userId=uinfo_mysql.userId,
            operationId=odata["operationId"],
            recordStatus=0
        ).all()
    except Exception as e:
        logmsg = "mysql中账户操作数据查询失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    for d in data:
        d.recordStatus = -1
    try:
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "mysql中账户操作数据更新失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    # 生成操作码
    code = str(
        uuid.uuid3(
            uuid.NAMESPACE_DNS, requestvalue_mail + str(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        )
    )
    # 将内容入库
    insertdata = model_mysql_useroperationrecord(
        userId=uinfo_mysql.userId,
        operationId=odata["operationId"],
        recordCode=code,
        recordStatus=0,
        recordValidTime=(datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    )
    try:
        mysqlpool.session.add(insertdata)
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "mysql中账户操作数据新增失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    # 发送重置密码邮件
    publicmailer.sendmail_reset_password(
        uinfo_mysql.userId,
        requestvalue_mail,
        code,
        odata["operationId"]
    )

    # 定义msg
    response_json["error_msg"] = "操作成功，请查收重置密码邮件"
    # 最后返回内容
    return response_json
