# -*- coding: utf-8 -*-

import flask
import route
import json

from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.log import api_logger
from handler.pool import mysqlpool

from model.redis import model_redis_rolepermission

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_rolepermission
from model.mysql import model_mysql_functioninfo


# 账户权限校验-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在，排除掉不存在的/已禁用的/未激活的
# 3.校验令牌是否有效
# ----操作
# 4.于redis中查询并返回permission配置信息
# 5.若redis中无，则去mysql中查询，然后写入redis
@route.check_token
@route.check_user
def user_permission_get():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 取出传入参数值
    requestvalue_id = int(flask.request.headers["UserId"])

    # 查询
    userdata = ApiCheck.check_user(user_id=requestvalue_id)
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

    # 查询权限信息
    rp = ApiCheck.check_role_permission(
        userdata['userRoleId']
    )
    if rp["exist"] is True:
        response_json["data"]["permission"] = rp["rolePermission"]
    elif rp["exist"] is False:
        response_json["data"]["permission"] = {}
    else:
        return ApiError.requestfail_server("角色权限信息处理异常")

    # 定义msg
    response_json["error_msg"] = "token有效"
    # 最后返回内容
    return response_json


# 根据传入的角色标识符判断角色是否存在以及角色的权限配置信息
# 如果在redis中查询成功，则返回角色权限配置信息
# 如果在redis中未查询到，则查询mysql，将结果写入redis后返回角色权限配置信息
# 如果在mysql中未查询到，则返回无角色信息
# 返回信息，第一位为有效位：
# 1.角色存在
# return {
#     "exist": True,
#     "roleId": roleId,
#     "rolePermission": rolePermission,
# }
# 2.角色不存在
# return {
#     "exist": False,
#     "roleId": None,
#     "rolePermission": None,
# }
# 3.数据处理异常
# return {
#     "exist": None,
#     "roleId": None,
#     "rolePermission": None,
# }
def check_role_permission(roleid):
    data = {
        "exist": None,
        "roleId": roleid,
        "rolePermission": {},
    }
    # 首先从缓存中查询角色权限信息
    try:
        rpermission_redis = model_redis_rolepermission.query(role_id=roleid)
        logmsg = "缓存中角色信息读取成功"
        api_logger.debug(logmsg)
    except Exception as e:
        logmsg = "缓存中角色信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        for d in data:
            data[d] = None
        return data
    # 如果缓存中查询到了
    if rpermission_redis is not None:
        # 格式化缓存角色权限信息内容
        try:
            data["rolePermission"] = json.loads(rpermission_redis.decode("utf8"))
            logmsg = "缓存中角色权限列表信息json格式化成功"
            api_logger.debug(logmsg)
        except Exception as e:
            logmsg = "缓存中角色权限列表信息json格式化失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            for d in data:
                data[d] = None
            return data
        else:
            data["exist"] = True
            return data
    # 如果缓存中未查询到
    else:
        # 尝试去mysql查询角色是否存在
        try:
            rinfo_mysql = model_mysql_roleinfo.query.filter_by(roleId=roleid).first()
            logmsg = "数据库中角色信息读取成功"
            api_logger.debug(logmsg)
        except Exception as e:
            logmsg = "数据库中角色信息读取失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            for d in data:
                data[d] = None
            return data
        # 如果mysql中未查询到
        if rinfo_mysql is None:
            # 返回
            for d in data:
                data[d] = None
            data["exist"] = False
            return data
        # 如果mysql中查询到了
        else:
            # 赋值角色基础信息
            data["exist"] = True
            # 尝试去mysql中查询最新的角色权限配置数据
            try:
                role_page_permission_data = mysqlpool.session.query(
                    model_mysql_rolepermission,
                    model_mysql_rolepermission.functionId,
                    model_mysql_functioninfo.functionAlias
                ).join(
                    model_mysql_functioninfo,
                    model_mysql_rolepermission.functionId == model_mysql_functioninfo.functionId
                ).filter(
                    model_mysql_rolepermission.roleId == roleid,
                    model_mysql_functioninfo.functionType == 1,
                    model_mysql_rolepermission.hasPermission == 1
                ).all()
                logmsg = "数据库中角色的页面权限配置数据读取成功"
                api_logger.debug(logmsg)
            except Exception as e:
                logmsg = "数据库中角色的页面权限配置数据读取失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                # 返回
                for d in data:
                    data[d] = None
                return data
            else:
                """拼接待缓存的权限数据
                    格式：
                    permission = {
                        "1": {
                            "id": 1,
                            "alias": "AAA",
                            "component": {
                                "2": {
                                    "id": 2,
                                    "alias": "BBB"
                                },
                                "4": {
                                    "id": 4,
                                    "alias": "DDD"
                                }
                            }
                        }
                    }
                """
                permission = {}
                for page_permission in role_page_permission_data:
                    permission[str(page_permission.functionId)] = {
                        "id": page_permission.functionId,
                        "alias": page_permission.functionAlias,
                        "component": {}
                    }
                    try:
                        role_component_permission_data = mysqlpool.session.query(
                            model_mysql_rolepermission,
                            model_mysql_rolepermission.functionId,
                            model_mysql_functioninfo.functionAlias
                        ).join(
                            model_mysql_functioninfo,
                            model_mysql_rolepermission.functionId == model_mysql_functioninfo.functionId
                        ).filter(
                            model_mysql_rolepermission.roleId == roleid,
                            model_mysql_functioninfo.rootId == page_permission.functionId,
                            model_mysql_functioninfo.functionType == 2,
                            model_mysql_rolepermission.hasPermission == 1
                        ).all()
                        logmsg = "数据库中角色的功能权限配置数据读取成功"
                        api_logger.debug(logmsg)
                    except Exception as e:
                        logmsg = "数据库中角色的功能权限配置数据读取失败，失败原因：" + repr(e)
                        api_logger.error(logmsg)
                        # 返回
                        for d in data:
                            data[d] = None
                        return data
                    else:
                        for component_permission in role_component_permission_data:
                            permission[str(page_permission.functionId)]["component"][
                                str(component_permission.functionId)] = {
                                "id": component_permission.functionId,
                                "alias": component_permission.functionAlias
                            }
                # 然后将需缓存的内容缓存至redis的rolePermission
                # 需缓存内容:
                # key=roleId
                # value=permission
                try:
                    model_redis_rolepermission.set(
                        roleid,
                        json.dumps(permission)
                    )
                except Exception as e:
                    logmsg = "缓存库中角色权限信息写入失败，失败原因：" + repr(e)
                    api_logger.error(logmsg)
                    # 返回
                    for d in data:
                        data[d] = None
                    return data
                else:
                    data["rolePermission"] = permission
                    return data