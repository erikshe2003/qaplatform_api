# -*- coding: utf-8 -*-

import flask
import json
import route

from handler.api.check import ApiCheck
from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_apiinfo
from model.mysql import model_mysql_functionorg
from model.mysql import model_mysql_rolepermission
from model.mysql import model_mysql_functioninfo

from model.redis import model_redis_rolepermission
from model.redis import model_redis_apiauth


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['role_name', str, 1, 20],
    ['role_description', str, 0, 100]
)
def role_post():
    """
        新增角色信息以及角色权限配置-api路由
        ----校验
                校验传参
                校验账户是否存在
                校验账户操作令牌
                校验账户是否有操作权限
        ----操作
                新增角色基础信息
                新增角色权限配置信息
                新增redis中的该角色的权限缓存数据(前端权限控制)
                新增redis中的该角色的权限缓存数据(后端权限控制)
    """
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    """
        校验传参
        取出请求参数
    """
    requestvalue_rolename = flask.request.json["role_name"]
    requestvalue_roledescription = flask.request.json["role_description"]
    
    # role_permission
    if "role_permission" not in flask.request.json:
        return route.error_msgs[302]['msg_request_params_incomplete']
    requestvalue_permission = flask.request.json['role_permission']
    # 检查必传项内容格式
    # role_permission
    if type(requestvalue_permission) is not dict:
        return route.error_msgs[301]['msg_request_params_illegal']
    """
        检查role_permission格式
        # 1.最上层为dict，已检查
        # 2.最上层dict内为多个子dict
        # 3.子dict内需至少包含id/has，用以更新权限数据
        # 4.子dict的component为dict
        # 5.子dict的component中的dict内至少包含id/has，用以更新权限数据
    """
    for rp in requestvalue_permission:
        if type(requestvalue_permission[rp]) is not dict:
            return route.error_msgs[301]['msg_request_params_illegal']
        if "id" not in requestvalue_permission[rp] or type(
                requestvalue_permission[rp]["id"]
        ) is not int or requestvalue_permission[rp]["id"] < 1:
            return route.error_msgs[301]['msg_request_params_illegal']
        if "has" not in requestvalue_permission[rp] or type(
                requestvalue_permission[rp]["has"]) is not bool:
            return route.error_msgs[301]['msg_request_params_illegal']
        if type(requestvalue_permission[rp]["component"]) is not dict:
            return route.error_msgs[301]['msg_request_params_illegal']
        cf = ApiCheck.check_function(rp, 0)
        if cf['exist'] is False:
            return route.error_msgs[301]['msg_request_params_illegal']
        elif cf['exist'] is None:
            return route.error_msgs[301]['msg_request_params_illegal']
        for rpc in requestvalue_permission[rp]["component"]:
            if type(requestvalue_permission[rp]["component"][rpc]) is not dict:
                return route.error_msgs[301]['msg_request_params_illegal']
            if "id" not in requestvalue_permission[rp]["component"][rpc] or type(
                    requestvalue_permission[rp]["component"][rpc]["id"]
            ) is not int or requestvalue_permission[rp]["component"][rpc]["id"] < 1:
                return route.error_msgs[301]['msg_request_params_illegal']
            if "has" not in requestvalue_permission[rp]["component"][rpc] or type(
                    requestvalue_permission[rp]["component"][rpc]["has"]) is not bool:
                return route.error_msgs[301]['msg_request_params_illegal']
            cf = ApiCheck.check_function(rpc, rp)
            if cf['exist'] is False:
                return route.error_msgs[301]['msg_request_params_illegal']
            elif cf['exist'] is None:
                return route.error_msgs[301]['msg_request_params_illegal']

    """ 
        4.新增角色基础信息
    """
    try:
        new_role_info = model_mysql_roleinfo(
            roleName=requestvalue_rolename,
            roleDescription=requestvalue_roledescription,
            roleIsAdmin=0,
            roleStatus=1
        )
        mysqlpool.session.add(new_role_info)
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "数据库中账号信息写入失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']

    """
        5.新增角色权限配置信息
    """
    for functionid_page in requestvalue_permission:
        # 新增page权限
        page_has_permission = 1 if requestvalue_permission[functionid_page]["has"] else 0
        page_role_permission = model_mysql_rolepermission(
            roleId=new_role_info.roleId,
            functionId=functionid_page,
            hasPermission=page_has_permission
        )
        mysqlpool.session.add(page_role_permission)

        # 新增component权限
        for functionid_component in requestvalue_permission[functionid_page]["component"]:
            component_has_permission = 1 if \
                requestvalue_permission[functionid_page]["component"][functionid_component]["has"] else 0
            component_role_permission = model_mysql_rolepermission(
                roleId=new_role_info.roleId,
                functionId=functionid_component,
                hasPermission=component_has_permission
            )
            mysqlpool.session.add(component_role_permission)

    try:
        mysqlpool.session.commit()
    except Exception as e:
        logmsg = "数据库中账号信息写入失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']

    """
        6.新增redis中的该角色的权限缓存数据(前端权限数据)
    """
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
            model_mysql_rolepermission.roleId == new_role_info.roleId,
            model_mysql_functioninfo.functionType == 1,
            model_mysql_rolepermission.hasPermission == 1
        ).all()
        logmsg = "数据库中角色权限信息修改后页面权限配置信息读取成功"
        api_logger.debug(logmsg)
    except Exception as e:
        logmsg = "数据库中角色权限信息修改后页面权限配置信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
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
                    model_mysql_rolepermission.roleId == new_role_info.roleId,
                    model_mysql_functioninfo.rootId == page_permission.functionId,
                    model_mysql_functioninfo.functionType == 2,
                    model_mysql_rolepermission.hasPermission == 1
                ).all()
                logmsg = "数据库中角色权限信息修改后功能权限配置信息读取成功"
                api_logger.debug(logmsg)
            except Exception as e:
                logmsg = "数据库中角色权限信息修改后功能权限配置信息读取失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                return route.error_msgs[500]['msg_db_error']
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
                new_role_info.roleId,
                json.dumps(permission)
            )
        except Exception as e:
            logmsg = "缓存库中角色权限信息写入失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return route.error_msgs[500]['msg_db_error']

    """
        7.新增redis中的该角色的权限缓存数据(后端权限数据)
    """
    # 尝试去mysql中查询最新的角色权限配置数据
    try:
        role_api_auth_data = mysqlpool.session.query(
            model_mysql_rolepermission,
            model_mysql_apiinfo.apiUrl,
            model_mysql_rolepermission.hasPermission
        ).join(
            model_mysql_functionorg,
            model_mysql_functionorg.functionId == model_mysql_rolepermission.functionId
        ).join(
            model_mysql_apiinfo,
            model_mysql_apiinfo.apiId == model_mysql_functionorg.apiId
        ).filter(
            model_mysql_rolepermission.roleId == new_role_info.roleId
        ).all()
        logmsg = "数据库中角色权限信息修改后页面权限配置信息读取成功"
        api_logger.debug(logmsg)
    except Exception as e:
        logmsg = "数据库中角色权限信息修改后页面权限配置信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
        return route.error_msgs[500]['msg_db_error']
    else:
        """
            拼接待缓存的权限数据
            格式：
            auth = {
                roleId: {
                    "/api/management/role/getRoleList.json": 1,
                    "/api/management/role/searchRole.json": 0
                }
            }
        """
        auth = {}
        for auth_data in role_api_auth_data:
            auth[auth_data.apiUrl] = auth_data.hasPermission

        # 然后将需缓存的内容缓存至redis的apiAuth
        # 需缓存内容:
        # key=roleId
        # value=auth
        try:
            model_redis_apiauth.set(
                new_role_info.roleId,
                json.dumps(auth)
            )
        except Exception as e:
            logmsg = "缓存库中角色权限信息写入失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return route.error_msgs[500]['msg_db_error']

    # 返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json
