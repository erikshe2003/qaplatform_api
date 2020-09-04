# -*- coding: utf-8 -*-

import flask
import re
import datetime
import uuid
import route

from handler.api.check import ApiCheck
from handler.mail import publicmailer
from handler.pool import mysqlpool
from handler.log import api_logger
from handler.config import appconfig

from model.mysql import model_mysql_userinfo
from model.mysql import model_mysql_useroperationrecord


# 基础信息修改-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验新账户是否存在，排除存在的场景
# ----操作
# 4.如果邮箱账户未变化，则不发送更改邮箱地址的邮件，不进行此操作
# 5.如果账户不存在，则提前生成操作码，尝试发送修改邮箱确认邮件。
# 如果邮件发送成功，修改操作记录，将之前的修改绑定邮箱的操作记录
# 置为-1，并在账号表中新增/覆盖userNewEmail字段内容
# 6.保存账户头像
# 7.修改账户昵称/个人简介
# 9.返回成功信息
@route.check_token
@route.check_user
@route.check_get_parameter(
    ['fileUrl', str, 1, None],
    ['userId', int, 1, None],
    ['newMailAddress', str, 1, 100],
    ['nickName', str, 1, 100],
    ['introduceContent', str, 1, 200]
)
def user_info_put():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "",
        "data": {}
    }

    # 取出参数
    rq_file_url = flask.request.json['fileUrl']
    rq_user_id = flask.request.json['userId']
    rq_new_mail_address = flask.request.json['newMailAddress']
    rq_nick_name = flask.request.json['nickName']
    rq_introduce = flask.request.json['introduceContent']

    # 校验传参
    # new_mail_address
    mail_reg = '^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$'
    if not re.search(mail_reg, rq_new_mail_address):
        return route.error_msgs[301]['msg_value_type_error']

    # 如果邮箱变更了，则需要检查新邮箱是否已被注册
    # 在库中获取账户信息，准备修改新邮箱信息
    try:
        user_info = model_mysql_userinfo.query.filter_by(
            userId=rq_user_id
        ).first()
    except Exception as e:
        api_logger.error("数据库账户数据查询失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        # 校验账户状态
        # 仅状态正常的账户支持信息修改
        if user_info is None:
            return route.error_msgs[201]['msg_no_user']
        elif user_info.userStatus == 1:
            pass
        elif user_info.userStatus == 0:
            return route.error_msgs[201]['msg_need_register']
        elif user_info.userStatus == -1:
            return route.error_msgs[201]['msg_user_forbidden']
        else:
            return route.error_msgs[500]['msg_server_error']

    # 检查传递邮箱
    # 如果已被注册则返回错误信息
    # 如果未被注册则将新邮箱地址入库并发送确认邮件
    if user_info.userEmail != rq_new_mail_address:
        # 校验新账户是否存在，排除存在的场景
        try:
            newuserdata = model_mysql_userinfo.query.filter_by(
                userEmail=rq_new_mail_address
            ).first()
        except Exception as e:
            api_logger.error("数据库账户数据查询失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if newuserdata is not None:
                return route.error_msgs[201]['msg_mail_exist']

        # 生成操作码，尝试发送修改邮箱确认邮件
        # 如果邮件发送成功，则在账号表中新增/覆盖userNewEmail字段内容
        # 查询关键操作唯一标识符
        odata = ApiCheck.check_operate(
            appconfig.get("operation_alias", "changeMail")
        )
        if odata["exist"] is True:
            pass
        elif odata["exist"] is False:
            return route.error_msgs[201]['msg_operation_alias_not_exist']
        else:
            return route.error_msgs[500]['msg_server_error']

        # 生成操作码
        code = str(
            uuid.uuid3(
                uuid.NAMESPACE_DNS, rq_new_mail_address + str(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
        )
        # 发送包含账户信息确认页链接的邮件
        # 先发送邮件，成功后再记录数据
        # 保证过滤掉不存在的邮件地址
        send_result_flag, send_result_type = publicmailer.sendmail_change_mail(
            rq_user_id,
            user_info.userEmail,
            rq_new_mail_address,
            code,
            3
        )
        # 如果发送失败，则返回错误信息
        if send_result_flag is False:
            if send_result_type == -1:
                return route.error_msgs[500]['msg_smtp_error']
            elif send_result_type == 1 or send_result_type == 2:
                return route.error_msgs[500]['msg_public_mail_login_fail']
            elif send_result_type == 3:
                return route.error_msgs[201]['msg_mail_send_fail']
        else:
            # 修改操作记录，将之前的修改绑定邮箱的操作记录置为-1
            try:
                rdata_mysql = model_mysql_useroperationrecord.query.filter_by(
                    userId=user_info.userId,
                    operationId=odata["operationId"],
                    recordStatus=0
                ).all()
            except Exception as e:
                api_logger.error("账户操作记录数据查询失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            # 如果查询到了，则全部置为无效
            if rdata_mysql is not None:
                for d in rdata_mysql:
                    d.recordStatus = -1
                try:
                    mysqlpool.session.commit()
                except Exception as e:
                    api_logger.error("账户操作记录数据更新失败，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']

            # 将新的操作码数据写入mysql
            insertdata = model_mysql_useroperationrecord(
                userId=user_info.userId,
                operationId=odata["operationId"],
                recordCode=code,
                recordStatus=0,
                recordValidTime=(datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            )
            try:
                mysqlpool.session.add(insertdata)
                mysqlpool.session.commit()
            except Exception as e:
                logmsg = "数据库新增申请修改绑定邮箱记录数据失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                return route.error_msgs[500]['msg_db_error']

        # 修改其新邮件地址信息
        user_info.userNewEmail = rq_new_mail_address

        # 变更邮箱需要变更返回信息
        response_json["msg"] = "基础信息修改成功，请于新邮箱查收修改绑定邮箱确认邮件"
    else:
        # 返回普通成功信息
        response_json["msg"] = "基础信息修改成功"

    # 修改头像地址/昵称/简介
    user_info.userHeadIconUrl = rq_file_url
    user_info.userNickName = rq_nick_name
    user_info.userIntroduction = rq_introduce
    # 尝试写入mysql
    try:
        mysqlpool.session.commit()
    except Exception as e:
        api_logger.error("账户信息存入数据库失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    # 最后返回内容
    return response_json
