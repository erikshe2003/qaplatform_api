# -*- coding: utf-8 -*-

import flask
import route

from sqlalchemy import and_

from handler.log import api_logger
from handler.api.check import ApiCheck

from model.mysql import model_mysql_userinfo


# 账户重置密码-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验操作码是否有效
# ----操作
# 4.返回校验数据
@route.check_get_parameter(
    ['user_id', int, 1, None],
    ['mail_address', str, 1, None],
    ['record_code', str, 1, None],
    ['operation_id', int, 1, None]
)
def key_action_code_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "",
        "data": {}
    }

    # 取出传入参数值
    requestvalue_id = int(flask.request.args["user_id"])
    requestvalue_mail = flask.request.args["mail_address"]
    requestvalue_recordcode = flask.request.args["record_code"]
    requestvalue_operateid = int(flask.request.args["operation_id"])

    # 2.校验账户是否存在
    userdata = ApiCheck.check_user(requestvalue_id)
    if userdata["exist"] is False:
        return route.error_msgs[201]['msg_no_user']
    elif userdata["exist"] is True and userdata["userStatus"] in [0, 1]:
        pass
    elif userdata["userStatus"] == -1:
        return route.error_msgs[201]['msg_no_user']
    else:
        return route.error_msgs[201]['msg_status_error']

    # 校验id与mail是否为同一人
    try:
        uinfo_mysql = model_mysql_userinfo.query.filter(
            and_(
                model_mysql_userinfo.userId == requestvalue_id,
                model_mysql_userinfo.userEmail == requestvalue_mail
            )
        ).first()
    except Exception as e:
        logmsg = "数据库中账户信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
    else:
        if not uinfo_mysql:
            return route.error_msgs[201]['msg_user_id_wrong']

    # 3.校验操作码是否有效
    codeexist, codevalid = ApiCheck.check_code(
        userdata["userId"],
        requestvalue_recordcode,
        requestvalue_operateid
    )
    if codeexist is False:
        return route.error_msgs[201]['action_code_non']
    elif codeexist is True and codevalid == 0:
        return route.error_msgs[201]['action_code_expire']
    elif codeexist is True and codevalid == 1:
        pass
    else:
        return route.error_msgs[201]["action_code_error"]

    # 4.返回校验数据
    response_json["msg"] = "账户操作码校验通过"
    # 最后返回内容
    return response_json
