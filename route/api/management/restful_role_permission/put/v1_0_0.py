# -*- coding: utf-8 -*-

import flask
import route
import datetime
import re
import json

from handler.api.error import ApiError
from handler.api.check import ApiCheck
from handler.log import api_logger, db_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_rolepermission
from model.mysql import model_mysql_functioninfo
from model.mysql import model_mysql_apiinfo
from model.mysql import model_mysql_functionorg

from model.redis import model_redis_rolepermission
from model.redis import model_redis_apiauth


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['role_id', int, 1, None],
    ['role_description', str, 0, 200]
)
def role_permission_put():
    """
        修改角色配置信息-api路由
        ----校验
        1.校验传参
        2.校验账户是否存在
        3.校验账户操作令牌
        4.校验角色是否存在
        5.校验角色权限是否可变更
        ----操作
        6.mysql逐条变更角色权限
        7.刷新redis中的该角色的权限缓存数据
    """
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    """
        1.校验传参
        取出请求参数
    """
    requestvalue_roleid = int(flask.request.json["role_id"])
    requestvalue_roledescription = flask.request.json["role_description"]
    # role_permission
    if "role_permission" not in flask.request.json:
        return ApiError.requestfail_nokey("role_permission")
    requestvalue_permission = flask.request.json["role_permission"]
    
    # 检查通过
    # 检查必传项内容格式
    # role_permission
    if type(requestvalue_permission) is not dict:
        return ApiError.requestfail_value("role_permission")
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
            return ApiError.requestfail_value("role_permission")
        if "id" not in requestvalue_permission[rp] or type(
                requestvalue_permission[rp]["id"]
        ) is not int or requestvalue_permission[rp]["id"] < 1:
            return ApiError.requestfail_value("role_permission")
        if "has" not in requestvalue_permission[rp] or type(
                requestvalue_permission[rp]["has"]) is not bool:
            return ApiError.requestfail_value("role_permission")
        if type(requestvalue_permission[rp]["component"]) is not dict:
            return ApiError.requestfail_value("role_permission")
        cf = ApiCheck.check_function(rp, 0)
        if cf['exist'] is False:
            return ApiError.requestfail_value("role_permission")
        elif cf['exist'] is None:
            return ApiError.requestfail_error("角色权限信息校验异常")
        for rpc in requestvalue_permission[rp]["component"]:
            if type(requestvalue_permission[rp]["component"][rpc]) is not dict:
                return ApiError.requestfail_value("role_permission")
            if "id" not in requestvalue_permission[rp]["component"][rpc] or type(
                    requestvalue_permission[rp]["component"][rpc]["id"]
            ) is not int or requestvalue_permission[rp]["component"][rpc]["id"] < 1:
                return ApiError.requestfail_value("role_permission")
            if "has" not in requestvalue_permission[rp]["component"][rpc] or type(
                    requestvalue_permission[rp]["component"][rpc]["has"]) is not bool:
                return ApiError.requestfail_value("role_permission")
            cf = ApiCheck.check_function(rpc, rp)
            if cf['exist'] is False:
                return ApiError.requestfail_value("role_permission")
            elif cf['exist'] is None:
                return ApiError.requestfail_error("角色权限信息校验异常")

    """
        6.mysql逐条变更角色权限
        先变更page的再变更部件的
    """
    for functionid_page in requestvalue_permission:
        """
            1.首先到rolePermission表中校验page的权限记录是否存在
            2.如果存在，再判断当前值和所要修改的值是否一致，不一致则update，否则pass
            3.且更新的时候，如果是从1改成0，则顺带要把该page下所有的部件权限全部改为0
            4.如果不存在，则insert
            5.然后更新component的权限配置，和page一样，有则改之无则insert
        """
        # 尝试获取某role的page权限配置数据
        try:
            """
                当使用filter时，数据筛选条件写条件表达式:A.a == b|A.a>b|A.a<b，且列需要写成表.列
                当使用filter_by时，数据筛选条件写关键字表达式:a=b，列直接写列名即可
                后续统一使用filter
            """
            pg_data = model_mysql_rolepermission.query.filter(
                model_mysql_rolepermission.roleId == requestvalue_roleid,
                model_mysql_rolepermission.functionId == functionid_page
            ).first()
        except Exception as e:
            logmsg = "数据库中角色的page访问权限获取失败：" + repr(e)
            api_logger.error(logmsg)
            return route.error_msgs[500]['msg_db_error']
        else:
            """
                如果获取到了，且数据库中记录的hasPermission字段值和传入的page的has值不等
                1==Ture
                2==False
                0==False
            """
            # 如果page的权限数据有并且权限数据和传入的不一致
            page_has = requestvalue_permission[functionid_page]["has"]
            if pg_data and pg_data.hasPermission != page_has:
                # 当数据库中记录的page权限配置为1时，要将数据改为0
                if pg_data.hasPermission == 1:
                    pg_data.hasPermission = 0
                    mysqlpool.session.commit()
                    # 然后查询page下的component权限配置
                    for functionid_component in requestvalue_permission[functionid_page]["component"]:
                        try:
                            cp_data = model_mysql_rolepermission.query.filter(
                                model_mysql_rolepermission.roleId == requestvalue_roleid,
                                model_mysql_rolepermission.functionId == functionid_component
                            ).first()
                        except Exception as e:
                            logmsg = "数据库中角色的页面下功能访问权限获取失败：" + repr(e)
                            api_logger.error(logmsg)
                            return route.error_msgs[500]['msg_db_error']
                        else:
                            if cp_data:
                                cp_data.hasPermission = 0
                            else:
                                cp_data = model_mysql_rolepermission(
                                    roleId=requestvalue_roleid,
                                    functionId=functionid_component,
                                    hasPermission=0
                                )
                                mysqlpool.session.add(cp_data)
                        mysqlpool.session.commit()
                else:
                    # 当数据库中记录的page权限配置为0时，要将数据改为1
                    pg_data.hasPermission = 1
                    mysqlpool.session.commit()
                    # 然后根据传入component权限配置数据，修改数据库中对应的数据
                    for functionid_component in requestvalue_permission[functionid_page]["component"]:
                        component_has = requestvalue_permission[functionid_page]["component"][functionid_component]["has"]
                        try:
                            cp_data = model_mysql_rolepermission.query.filter(
                                model_mysql_rolepermission.roleId == requestvalue_roleid,
                                model_mysql_rolepermission.functionId == functionid_component
                            ).first()
                        except Exception as e:
                            logmsg = "数据库中角色的页面下功能访问权限获取失败：" + repr(e)
                            api_logger.error(logmsg)
                            return route.error_msgs[500]['msg_db_error']
                        else:
                            # 如果component的权限配置数据有，并且数据库中记录的权限配置和传入的数据不一致
                            if cp_data and cp_data.hasPermission != component_has:
                                # 修改数据库中的值
                                cp_data.hasPermission = 0 if cp_data.hasPermission == 1 else 1
                                mysqlpool.session.commit()
                            # 如果component的权限配置数据有，并且数据库中记录的权限配置和传入的数据一致
                            elif cp_data and cp_data.hasPermission == component_has:
                                pass
                            # 如果component的权限配置数据没有
                            else:
                                # 新增component权限配置数据
                                cp_data = model_mysql_rolepermission(
                                    roleId=requestvalue_roleid,
                                    functionId=functionid_component,
                                    hasPermission=1 if component_has else 0
                                )
                                mysqlpool.session.add(cp_data)
                                mysqlpool.session.commit()
            # 如果page的权限数据有并且和传入的一致
            elif pg_data and pg_data.hasPermission == page_has:
                # 校验component的权限配置
                # 然后根据传入component权限配置数据，修改数据库中对应的数据
                for functionid_component in requestvalue_permission[functionid_page]["component"]:
                    component_has = requestvalue_permission[functionid_page]["component"][functionid_component]["has"]
                    try:
                        cp_data = model_mysql_rolepermission.query.filter(
                            model_mysql_rolepermission.roleId == requestvalue_roleid,
                            model_mysql_rolepermission.functionId == functionid_component
                        ).first()
                    except Exception as e:
                        logmsg = "数据库中角色的页面下功能访问权限获取失败：" + repr(e)
                        api_logger.error(logmsg)
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        # 如果component的权限配置数据有，并且数据库中记录的权限配置和传入的数据不一致
                        if cp_data and cp_data.hasPermission != component_has:
                            # 修改数据库中的值
                            cp_data.hasPermission = 0 if cp_data.hasPermission == 1 else 1
                            mysqlpool.session.commit()
                        # 如果component的权限配置数据有，并且数据库中记录的权限配置和传入的数据一致
                        elif cp_data and cp_data.hasPermission == component_has:
                            pass
                        # 如果component的权限配置数据没有
                        else:
                            # 新增component权限配置数据
                            cp_data = model_mysql_rolepermission(
                                roleId=requestvalue_roleid,
                                functionId=functionid_component,
                                hasPermission=1 if component_has else 0
                            )
                            mysqlpool.session.add(cp_data)
                            mysqlpool.session.commit()
            # 如果page的权限数据无
            else:
                # 新增page权限数据
                pg_data = model_mysql_rolepermission(
                    roleId=requestvalue_roleid,
                    functionId=functionid_page,
                    hasPermission=1 if page_has else 0
                )
                mysqlpool.session.add(pg_data)
                mysqlpool.session.commit()
                # 遍历传入的page下component的functionId
                for functionid_component in requestvalue_permission[functionid_page]["component"]:
                    component_has = requestvalue_permission[functionid_page]["component"][functionid_component]["has"]
                    try:
                        cp_data = model_mysql_rolepermission.query.filter(
                            model_mysql_rolepermission.roleId == requestvalue_roleid,
                            model_mysql_rolepermission.functionId == functionid_component
                        ).first()
                    except Exception as e:
                        logmsg = "数据库中角色的页面下功能访问权限获取失败：" + repr(e)
                        api_logger.error(logmsg)
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        # 如果component权限配置数据有且和传入的不一致
                        if cp_data and cp_data.hasPermission != component_has:
                            # 修改
                            cp_data.hasPermission = 0 if cp_data.hasPermission == 1 else 1
                            mysqlpool.session.commit()
                        # 如果component权限配置数据有且和传入的一致
                        elif cp_data and cp_data.hasPermission == component_has:
                            pass
                        # 如果component权限配置数据无
                        else:
                            # 新增component权限配置数据
                            cp_data = model_mysql_rolepermission(
                                roleId=requestvalue_roleid,
                                functionId=functionid_component,
                                hasPermission=1 if component_has else 0,
                            )
                            mysqlpool.session.add(cp_data)
                            mysqlpool.session.commit()
    # 更新角色说明
    try:
        model_mysql_roleinfo.query.filter(
            model_mysql_roleinfo.roleId == requestvalue_roleid
        ).update({
            model_mysql_roleinfo.roleDescription: requestvalue_roledescription,
            model_mysql_roleinfo.roleUpdateTime: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        mysqlpool.session.commit()
    except Exception as e:
        db_logger.error("数据库中角色的更新时间更新失败：" + repr(e))
        return route.error_msgs[500]['msg_db_update_error']

    """
        7.刷新redis中的该角色的权限缓存数据
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
            model_mysql_rolepermission.roleId == requestvalue_roleid,
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
                    model_mysql_rolepermission.roleId == requestvalue_roleid,
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
                    permission[str(page_permission.functionId)]["component"][str(component_permission.functionId)] = {
                        "id": component_permission.functionId,
                        "alias": component_permission.functionAlias
                    }
        # 然后将需缓存的内容缓存至redis的rolePermission
        # 需缓存内容:
        # key=roleId
        # value=permission
        try:
            model_redis_rolepermission.set(
                requestvalue_roleid,
                json.dumps(permission)
            )
        except Exception as e:
            logmsg = "缓存库中角色权限信息写入失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return route.error_msgs[500]['msg_db_error']

    # 将缓存中的旧数据替换为新数据
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
            model_mysql_rolepermission.roleId == requestvalue_roleid
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
                requestvalue_roleid,
                json.dumps(auth)
            )
        except Exception as e:
            logmsg = "缓存库中角色权限信息写入失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return route.error_msgs[500]['msg_db_error']

    # 8.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json
