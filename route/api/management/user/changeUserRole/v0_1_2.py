# -*- coding: utf-8 -*-

import flask
import re
import json

from sqlalchemy import func

from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.log import api_logger
from handler.pool import mysqlpool

from route.api.management.user import api_management_user

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_userinfo

from model.redis import model_redis_userinfo

"""
    修改账户所属角色-api路由
    ----校验
    1.校验传参
    2.校验账户是否存在
    3.校验账户操作令牌
    4.校验所操作的账户是否存在
    5.校验所操作的账户所属角色是否是超级管理员
    6.校验所操作的角色是否存在
    7.校验所操作的角色是否是超级管理员角色
    ----操作
    8.修改mysql账户所属角色
    9.修改redis账户所属角色
"""


@api_management_user.route('/changeUserRole.json', methods=["post"])
def change_user_role():
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
        logmsg = "/changeUserRole.json数据格式化失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_error("接口数据异常")
    else:
        if request_json is None:
            return ApiError.requestfail_error("接口数据异常")
    # 检查必传项是否遗留
    # mail_address
    if "mail_address" not in request_json:
        return ApiError.requestfail_nokey("mail_address")
    # user_token
    if "user_token" not in request_json:
        return ApiError.requestfail_nokey("user_token")
    # user_id
    if "user_id" not in request_json:
        return ApiError.requestfail_nokey("user_id")
    # role_id
    if "role_id" not in request_json:
        return ApiError.requestfail_nokey("role_id")
    # 检查通过
    # 检查必传项内容格式
    # mail_address
    if type(request_json["mail_address"]) is not str or len(request_json["mail_address"]) > 100:
        return ApiError.requestfail_value("mail_address")
    if re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_json["mail_address"]) is None:
        return ApiError.requestfail_value("mail_address")
    # user_token
    if type(request_json["user_token"]) is not str or len(request_json["user_token"]) > 100:
        return ApiError.requestfail_value("user_token")
    # user_id
    if type(request_json["user_id"]) is not int or request_json["user_id"] < 1:
        return ApiError.requestfail_value("user_id")
    # role_id
    if type(request_json["role_id"]) is not int or request_json["role_id"] < 0:
        return ApiError.requestfail_value("role_id")

    # 取出传入参数值
    requestvalue_mail = request_json["mail_address"]
    requestvalue_token = request_json["user_token"]
    requestvalue_userid = request_json["user_id"]
    requestvalue_roleid = request_json["role_id"]

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

    # 4.校验账户所属角色是否具有后端权限
    cr = ApiCheck.check_auth(
        roleid=userdata["userRoleId"],
        apiurl="changeUserRole.json"
    )
    if cr["exist"] is True and cr["pass"] is True:
        pass
    elif cr["exist"] is True and cr["pass"] is False:
        return ApiError.requestfail_error("账户所属角色无访问权限")
    elif cr["exist"] is False:
        return ApiError.requestfail_error("账户所属角色不存在")
    else:
        return ApiError.requestfail_error("角色权限配置校验异常")

    # 4.校验所操作的账户是否存在
    # 5.校验所操作的账户所属角色是否是超级管理员
    try:
        ur_data = mysqlpool.session.query(
            model_mysql_userinfo,
            model_mysql_userinfo.userId,
            model_mysql_roleinfo.roleIsAdmin
        ).join(
            model_mysql_roleinfo,
            model_mysql_roleinfo.roleId == model_mysql_userinfo.userRoleId,
            isouter=True
        ).filter(
            model_mysql_userinfo.userId == requestvalue_userid
        ).first()
    except Exception as e:
        logmsg = "数据库中账号数据读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    else:
        if ur_data and ur_data.roleIsAdmin == 1:
            return ApiError.requestfail_error("管理员账号禁止修改所属角色")
        elif ur_data:
            pass
        else:
            return ApiError.requestfail_error("账号不存在")

    # 如果传入的roleId为0，则将当前账户的所属角色去除
    if requestvalue_roleid != 0:
        # 6.校验所操作的角色是否存在
        # 7.校验所操作的角色是否是超级管理员角色
        try:
            ri_data = model_mysql_roleinfo.query.filter(
                model_mysql_roleinfo.roleId == requestvalue_roleid
            ).first()
        except Exception as e:
            logmsg = "数据库中角色数据读取失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return ApiError.requestfail_server(logmsg)
        else:
            if ri_data and ri_data.roleIsAdmin == 0:
                pass
            elif ri_data and ri_data.roleIsAdmin == 1:
                return ApiError.requestfail_error("管理员角色禁止操作")
            else:
                return ApiError.requestfail_error("角色不存在")

    # 8.修改mysql账户所属角色
    try:
        u_data = model_mysql_userinfo.query.filter(
            model_mysql_userinfo.userId == requestvalue_userid
        ).first()
        logmsg = "数据库中账号数据读取成功"
        api_logger.debug(logmsg)
    except Exception as e:
        logmsg = "数据库中账号数据读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)
    else:
        u_data.userRoleId = None if requestvalue_roleid == 0 else requestvalue_roleid
        mysqlpool.session.commit()

    # 9.修改redis账户所属角色
    cacheresult = model_redis_userinfo.set(
        u_data.userEmail,
        "{\"userId\":" + str(u_data.userId) +
        ",\"userNickName\":" + (
            "\"" + str(u_data.userNickName) + "\"" if u_data.userNickName is not None else "null"
        ) +
        ",\"userPassword\":" + (
            "\"" + str(u_data.userPassword) + "\"" if u_data.userPassword is not None else "null"
        ) +
        ",\"userStatus\":" + str(u_data.userStatus) +
        ",\"userRoleId\":" + (
            str(u_data.userRoleId) if u_data.userRoleId is not None else "null"
        ) + "}"
    )
    if cacheresult is True:
        pass
    else:
        logmsg = "账号基础信息写缓存失败"
        api_logger.error(logmsg)
        return ApiError.requestfail_server(logmsg)

    # 返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return json.dumps(response_json)

