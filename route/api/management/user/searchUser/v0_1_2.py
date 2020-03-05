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


"""
    获取包含账户基础信息的列表-api路由
    ----校验
    1.校验传参
    2.校验账户是否存在
    3.校验账户操作令牌
    ----操作
    4.join查询包含所属角色的账户基础信息，
    包括id/nickname/email/status/roleid/rolename/registertime/candelete/canmanage
"""


@api_management_user.route('/searchUser.json', methods=["post"])
def search_user():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {
            "total": 0,
            "user_list": {}
        }
    }

    # 1.校验传参
    # 取出请求参数
    try:
        request_json = flask.request.json
    except Exception as e:
        logmsg = "/searchUser.json数据格式化失败，失败原因：" + repr(e)
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
    # key_word
    if "key_word" not in request_json:
        return ApiError.requestfail_nokey("key_word")
    # status
    if "status" not in request_json:
        return ApiError.requestfail_nokey("status")
    # role_id
    if "role_id" not in request_json:
        return ApiError.requestfail_nokey("role_id")
    # page_num
    if "page_num" not in request_json:
        return ApiError.requestfail_nokey("page_num")
    # per_page
    if "per_page" not in request_json:
        return ApiError.requestfail_nokey("per_page")
    # 检查通过
    # 检查必传项内容格式
    # mail_address
    if type(request_json["mail_address"]) is not str or len(request_json["mail_address"]) > 100:
        return ApiError.requestfail_value("mail_address")
    if re.search("^[0-9a-zA-Z_]{1,100}@fclassroom.com$", request_json["mail_address"]) is None:
        return ApiError.requestfail_value("mail_address")
    # record_code
    if type(request_json["user_token"]) is not str or len(request_json["user_token"]) > 100:
        return ApiError.requestfail_value("user_token")
    # key_word
    if type(request_json["key_word"]) is not str or len(request_json["key_word"]) > 100:
        return ApiError.requestfail_value("key_word")
    # status
    if type(request_json["status"]) is not int or request_json["status"] not in [10, 1, 0, -1, -2]:
        return ApiError.requestfail_value("status")
    # role_id
    if type(request_json["role_id"]) is not int or request_json["role_id"] < 0:
        return ApiError.requestfail_value("role_id")
    # page_num
    if type(request_json["page_num"]) is not int or request_json["page_num"] < 1:
        return ApiError.requestfail_value("page_num")
    # per_page
    if type(request_json["per_page"]) is not int or request_json["per_page"] < 1:
        return ApiError.requestfail_value("per_page")

    # 取出传入参数值
    requestvalue_mail = request_json["mail_address"]
    requestvalue_token = request_json["user_token"]
    requestvalue_keyword = request_json["key_word"]
    requestvalue_status = request_json["status"]
    requestvalue_roleid = request_json["role_id"]
    requestvalue_num = request_json["page_num"]
    requestvalue_per = request_json["per_page"]

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
        apiurl="searchUser.json"
    )
    if cr["exist"] is True and cr["pass"] is True:
        pass
    elif cr["exist"] is True and cr["pass"] is False:
        return ApiError.requestfail_error("账户所属角色无访问权限")
    elif cr["exist"] is False:
        return ApiError.requestfail_error("账户所属角色不存在")
    else:
        return ApiError.requestfail_error("角色权限配置校验异常")

    # 4.join查询包含所属角色的账户基础信息，
    # 包括id/nickname/email/status/roleid/rolename/registertime/candelete/canmanage
    # 需添加filter条件
    # keyword模糊搜索userEmail
    # status为10则不搜索，为其他则精确匹配
    # role_id为0则不搜索，为其他则精确匹配
    try:
        uinfo_mysql = mysqlpool.session.query(
            model_mysql_userinfo,
            model_mysql_userinfo.userId,
            model_mysql_userinfo.userNickName,
            model_mysql_userinfo.userEmail,
            model_mysql_userinfo.userStatus,
            model_mysql_userinfo.userRoleId,
            model_mysql_roleinfo.roleName,
            model_mysql_userinfo.userRegisterTime,
            model_mysql_roleinfo.roleIsAdmin
        ).join(
            model_mysql_roleinfo,
            model_mysql_roleinfo.roleId == model_mysql_userinfo.userRoleId,
            isouter=True
        ).filter(
            model_mysql_userinfo.userEmail.like('%' + requestvalue_keyword + '%'),
        )
        if requestvalue_status == 10:
            pass
        else:
            uinfo_mysql = uinfo_mysql.filter(
                model_mysql_userinfo.userStatus == requestvalue_status
            )
        if requestvalue_roleid == 0:
            pass
        else:
            uinfo_mysql = uinfo_mysql.filter(
                model_mysql_userinfo.userRoleId == requestvalue_roleid
            )
        uinfo_mysql = uinfo_mysql.limit(
            # (requestvalue_num - 1) * requestvalue_per,
            requestvalue_per
        ).offset(
            (requestvalue_num - 1) * requestvalue_per
        ).all()
    except Exception as e:
        logmsg = "数据库中账号列表读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 构造user_list
        for u in uinfo_mysql:
            usome = {
                "id": u.userId,
                "nick_name": u.userNickName,
                "email": u.userEmail,
                "status": u.userStatus,
                "role_id": u.userRoleId,
                "role_name": u.roleName,
                "register_time": str(u.userRegisterTime) if u.userRegisterTime else u.userRegisterTime,
                "can_manage": False if u.roleIsAdmin else True,
                "can_delete": False if u.roleIsAdmin else True
            }
            response_json["data"]["user_list"][u.userId] = usome

    try:
        total_mysql = mysqlpool.session.query(
            func.count(model_mysql_userinfo.userId).label(name="userNum")
        ).first()
        logmsg = "数据库中账号总数读取成功"
        api_logger.debug(logmsg)
    except Exception as e:
        logmsg = "数据库中账号总数读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 构造total
        response_json["data"]["total"] = total_mysql.userNum

    # 8.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return json.dumps(response_json)

