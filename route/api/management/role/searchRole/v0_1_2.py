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
from model.mysql import model_mysql_userinfo


# 按关键字模糊搜索角色-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验账户操作令牌
# ----操作
# 4.查询角色，包括id/name/addtime/updatetime/canmanage
# 5.根据角色id，查询角色下关联的账户，判断角色是否可删除
# 6.根据角色isAdmin，判断角色是否可管理
# 7.查询角色的总数
@api_management_role.route('/searchRole.json', methods=["post"])
def search_role():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {
            "total": 0,
            "role_list": {

            }
        }
    }

    # 1.校验传参
    # 取出请求参数
    try:
        request_json = flask.request.json
    except Exception as e:
        logmsg = "/searchRole.json数据格式化失败，失败原因：" + repr(e)
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

    # 取出传入参数值
    requestvalue_mail = request_json["mail_address"]
    requestvalue_token = request_json["user_token"]
    requestvalue_keyword = request_json["key_word"]

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
        apiurl="searchRole.json"
    )
    if cr["exist"] is True and cr["pass"] is True:
        pass
    elif cr["exist"] is True and cr["pass"] is False:
        return ApiError.requestfail_error("账户所属角色无访问权限")
    elif cr["exist"] is False:
        return ApiError.requestfail_error("账户所属角色不存在")
    else:
        return ApiError.requestfail_error("角色权限配置校验异常")

    # 4.查询角色，包括id/name/addtime/updatetime/canmanage
    # 5.根据角色id，查询角色下关联的账户，判断角色是否可删除
    try:
        rinfo_mysql = mysqlpool.session.query(
            model_mysql_roleinfo,
            model_mysql_roleinfo.roleId,
            model_mysql_roleinfo.roleName,
            model_mysql_roleinfo.roleDescription,
            model_mysql_roleinfo.roleIsAdmin,
            model_mysql_roleinfo.roleAddTime,
            model_mysql_roleinfo.roleUpdateTime,
            func.count(model_mysql_userinfo.userId).label("userNum")
        ).join(
            model_mysql_userinfo,
            model_mysql_roleinfo.roleId == model_mysql_userinfo.userRoleId,
            isouter=True
        ).group_by(
            model_mysql_roleinfo.roleId
        ).filter(
            model_mysql_roleinfo.roleName.like('%' + requestvalue_keyword + '%')
        ).all()
    except Exception as e:
        logmsg = "数据库中角色列表读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 构造role_list
        for r in rinfo_mysql:
            rsome = {
                "id": r.roleId,
                "name": r.roleName,
                "description": r.roleDescription,
                "can_manage": True if r.roleIsAdmin == 0 else False,
                "can_delete": True if r.userNum == 0 else False,
                "add_time": str(r.roleAddTime),
                "update_time": str(r.roleUpdateTime)
            }
            response_json["data"]["role_list"][r.roleId] = rsome

    try:
        total_mysql = mysqlpool.session.query(
            model_mysql_roleinfo,
            func.count(model_mysql_roleinfo.roleId).label("roleNum"),
        ).first()
    except Exception as e:
        logmsg = "数据库中角色列表读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 构造total
        response_json["data"]["total"] = total_mysql.roleNum
    # 8.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return json.dumps(response_json)

