# -*- coding: utf-8 -*-

import flask
import re
import json

from sqlalchemy import func

from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.log import api_logger
from handler.pool import mysqlpool

from route.api.management.role import api_management_role

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_rolepermission
from model.redis import model_redis_rolepermission
from model.redis import model_redis_apiauth


# 删除角色-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验账户操作令牌
# 4.校验账户所属角色是否有此api的访问权限
# ----操作
# 4.检查角色是否存在
# 5.检查角色是否可删除
# 6.根据id删除角色
@api_management_role.route('/deleteRole.json', methods=["post"])
def delete_role():
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
        logmsg = "/getRoleList.json数据格式化失败，失败原因：" + repr(e)
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
    # role_id
    if type(request_json["role_id"]) is not int or request_json["role_id"] < 1:
        return ApiError.requestfail_value("role_id")

    # 取出传入参数值
    requestvalue_mail = request_json["mail_address"]
    requestvalue_token = request_json["user_token"]
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
        apiurl="deleteRole.json"
    )
    if cr["exist"] is True and cr["pass"] is True:
        pass
    elif cr["exist"] is True and cr["pass"] is False:
        return ApiError.requestfail_error("账户所属角色无访问权限")
    elif cr["exist"] is False:
        return ApiError.requestfail_error("账户所属角色不存在")
    else:
        return ApiError.requestfail_error("角色权限配置校验异常")

    # 4.检查角色是否存在
    # 5.检查角色是否可删除
    rl = ApiCheck.check_role(requestvalue_roleid)
    if rl["exist"] is True and rl["roleCanDelete"] is True:
        pass
    elif rl["exist"] is True and rl["roleCanDelete"] is False:
        return ApiError.requestfail_error("角色禁止删除")
    elif rl["exist"] is False:
        return ApiError.requestfail_error("角色不存在")
    else:
        return ApiError.requestfail_server("角色校验失败")

    # 5.尝试按照id删除角色以及角色的权限信息
    # 先删除mysql中roleInfo的信息
    try:
        ri_mysql = model_mysql_roleinfo.query.filter_by(roleId=requestvalue_roleid).all()
        logmsg = "数据库中账号信息读取成功"
        api_logger.error(logmsg)
    except Exception as e:
        logmsg = "数据库中账号信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 删
        [mysqlpool.session.delete(rim) for rim in ri_mysql]
        mysqlpool.session.commit()
    # 然后删除mysql中rolePermission的信息
    try:
        rp_mysql = model_mysql_rolepermission.query.filter_by(roleId=requestvalue_roleid).all()
        logmsg = "数据库中角色权限信息读取成功"
        api_logger.error(logmsg)
    except Exception as e:
        logmsg = "数据库中角色权限信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 删
        [mysqlpool.session.delete(rpm) for rpm in rp_mysql]
        mysqlpool.session.commit()
    # 删除redis中rolePermission的信息
    deleteflag = model_redis_rolepermission.delete(role_id=requestvalue_roleid)
    if deleteflag is True:
        logmsg = "缓存中角色权限信息删除成功"
        api_logger.debug(logmsg)
    else:
        logmsg = "缓存中角色权限信息删除失败"
        api_logger.error(logmsg)
    # 删除redis中apiAuth的信息
    deleteflag = model_redis_apiauth.delete(role_id=requestvalue_roleid)
    if deleteflag is True:
        logmsg = "缓存中角色权限信息删除成功"
        api_logger.debug(logmsg)
    else:
        logmsg = "缓存中角色权限信息删除失败"
        api_logger.error(logmsg)

    # 8.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return json.dumps(response_json)

