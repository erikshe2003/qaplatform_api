# -*- coding: utf-8 -*-

import json
import datetime

from sqlalchemy import func

from handler.log import api_logger
from handler.pool import mysqlpool

from model.redis import model_redis_userinfo
from model.redis import model_redis_rolepermission
from model.redis import model_redis_apiauth
from model.redis import model_redis_usertoken

from model.mysql import model_mysql_userinfo, model_mysql_useroperationrecord
from model.mysql import model_mysql_roleinfo, model_mysql_rolepermission
from model.mysql import model_mysql_operationinfo
from model.mysql import model_mysql_functioninfo
from model.mysql import model_mysql_functionorg
from model.mysql import model_mysql_apiinfo


class ApiCheck:
    # 根据传入的login_name判断账户信息在redis以及mysql中是否存在
    # 如果在redis中查询成功，则返回账户信息
    # 如果在redis中未查询到，则查询mysql，将结果写入redis后返回账户信息
    # 如果在mysql中未查询到，则返回无账户信息
    # 返回信息，第一位为有效位：
    # 1.账户存在
    # return {
    #     "exist": True,
    #     "userId": userId,
    #     "userEmail": userEmail,
    #     "userPassword": userPassword,
    #     "userStatus": userStatus,
    #     "userRoleId": userRoleId
    # }
    # 2.账户不存在
    # return {
    #     "exist": False,
    #     "userId": None,
    #     "userEmail": None,
    #     "userPassword": None,
    #     "userStatus": None,
    #     "userRoleId": None
    # }
    # 3.数据处理异常
    # return {
    #     "exist": None,
    #     "userId": None,
    #     "userEmail": None,
    #     "userPassword": None,
    #     "userStatus": None,
    #     "userRoleId": None
    # }
    @classmethod
    def check_user(cls, user_id):
        data = {
            "exist": None,
            "userId": None,
            "userLoginName": None,
            "userNickName": None,
            "userEmail": None,
            "userPassword": None,
            "userStatus": None,
            "userRoleId": None
        }
        # 校验账户状态
        # 从缓存中查询账户基础信息
        try:
            uinfo_redis = model_redis_userinfo.query(user_id=user_id)
        except Exception as e:
            logmsg = "缓存中账户信息读取失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return data
        # 如果缓存中查询到了
        if uinfo_redis is not None:
            # 格式化缓存基础信息内容
            try:
                uinfo = json.loads(uinfo_redis.decode("utf8"))
                logmsg = "缓存中账户信息json格式化成功"
                api_logger.debug(logmsg)
                data["exist"] = True
                data["userId"] = uinfo["userId"]
                data["userLoginName"] = uinfo["userLoginName"]
                data["userNickName"] = uinfo["userNickName"]
                data["userEmail"] = uinfo["userEmail"]
                data["userPassword"] = uinfo["userPassword"]
                data["userStatus"] = uinfo["userStatus"]
                data["userRoleId"] = uinfo["userRoleId"]
                # 返回账户信息
                return data
            except Exception as e:
                logmsg = "缓存中账户信息json格式化失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                for d in data:
                    data[d] = None
                return data
        # 如果缓存中未查询到
        else:
            # 尝试从mysql中查询
            try:
                uinfo_mysql = model_mysql_userinfo.query.filter_by(userId=user_id).first()
            except Exception as e:
                logmsg = "数据库中账户信息读取失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                for d in data:
                    data[d] = None
                return data
            # 如果mysql中未查询到
            if uinfo_mysql is None:
                # 返回
                data["exist"] = False
                return data
            # 如果mysql中查询到了
            else:
                # 将需缓存的内容缓存至redis的userInfo
                # 需缓存内容:
                # key=userEmail
                # value="\"userId\": int,
                #   \"userNickName\":str,
                #   \"userPassword\":str,
                #   \"userStatus\":int,
                #   \"userRoleId\":int"
                try:
                    model_redis_userinfo.set(
                        user_id,
                        "{\"userId\":" + str(uinfo_mysql.userId) +
                        ",\"userEmail\":" + (
                            "\"" + str(
                                uinfo_mysql.userEmail) + "\"" if uinfo_mysql.userEmail is not None else "null"
                        ) +
                        ",\"userLoginName\":" + (
                            "\"" + str(uinfo_mysql.userLoginName) + "\"" if uinfo_mysql.userLoginName is not None else "null"
                        ) +
                        ",\"userNickName\":" + (
                            "\"" + str(uinfo_mysql.userNickName) + "\"" if uinfo_mysql.userNickName is not None else "null"
                        ) +
                        ",\"userPassword\":" + (
                            "\"" + str(uinfo_mysql.userPassword) + "\"" if uinfo_mysql.userPassword is not None else "null"
                        ) +
                        ",\"userStatus\":" + str(uinfo_mysql.userStatus) +
                        ",\"userRoleId\":" + (
                            str(uinfo_mysql.userRoleId) if uinfo_mysql.userRoleId is not None else "null"
                        ) + "}"
                    )
                    # 返回账户信息
                    data["exist"] = True
                    data["userId"] = uinfo_mysql.userId
                    data["userLoginName"] = uinfo_mysql.userLoginName
                    data["userNickName"] = uinfo_mysql.userNickName
                    data["userEmail"] = uinfo_mysql.userEmail
                    data["userPassword"] = uinfo_mysql.userPassword
                    data["userStatus"] = uinfo_mysql.userStatus
                    data["userRoleId"] = uinfo_mysql.userRoleId
                    return data
                except Exception as e:
                    logmsg = "账户信息存入缓存失败，失败原因：" + repr(e)
                    api_logger.error(logmsg)
                    for d in data:
                        data[d] = None
                    return data

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
    @classmethod
    def check_role_permission(cls, roleid):
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

    # 根据传入的角色标识符判断角色在mysql中是否存在
    # 如果在mysql中未查询到，则返回无角色信息
    # 返回信息，第一位为有效位：
    # 1.角色存在
    # return {
    #     "exist": True,
    #     "roleId": roleId,
    #     "roleName": roleName,
    #     "roleStatus": roleStatus,
    #     "roleCanManage": boolen,
    #     "roleCanDelete": boolen
    # }
    # 2.角色不存在
    # return {
    #     "exist": False,
    #     "roleId": None,
    #     "roleName": None,
    #     "roleStatus": None,
    #     "roleCanManage": None,
    #     "roleCanDelete": None
    # }
    # 3.数据处理异常
    # return {
    #     "exist": None,
    #     "roleId": None,
    #     "roleName": None,
    #     "roleStatus": None,
    #     "roleCanManage": None,
    #     "roleCanDelete": None
    # }
    @classmethod
    def check_role(cls, roleid):
        data = {
            "exist": None,
            "roleId": None,
            "roleName": None,
            "roleCanManage": None,
            "roleCanDelete": None
        }

        # 5.根据角色id，查询角色下关联的账户
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
                model_mysql_roleinfo.roleId == roleid
            ).first()
        except Exception as e:
            logmsg = "数据库中角色列表读取失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
        else:
            if rinfo_mysql is None:
                data["exist"] = False
            else:
                data["exist"] = True
                data["roleId"] = rinfo_mysql.roleId
                data["roleName"] = rinfo_mysql.roleName
                data["roleCanManage"] = True if rinfo_mysql.roleIsAdmin == 0 else False
                data["roleCanDelete"] = True if rinfo_mysql.userNum == 0 else False
        return data

    # 根据传入的账户标识符/操作码/操作类型来判断操作码是否有效
    # 只查询mysql
    # 如果有记录且操作码未过期，则返回正确信息
    # 如果有记录但操作码已过期，则返回已过期
    # 如果无记录，则返回无记录
    # 返回信息，第一位为有效位：
    # return True, 1 操作码有效
    # return True, 0 操作码过期
    # return False, None 操作码错误或不存在
    # return None, None 数据处理异常
    @classmethod
    def check_code(cls, userid, code, operationid):
        # 校验账户的操作记录
        # 查询mysql
        try:
            rdata_mysql = model_mysql_useroperationrecord.query.filter_by(
                userId=userid,
                operationId=operationid,
                recordStatus=0
            ).first()
        except Exception as e:
            logmsg = "数据库中账户操作记录读取失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
            return None, None
        # 如果未查询到
        if rdata_mysql is None:
            return False, None
        # 如果查询到了
        else:
            record_code = rdata_mysql.recordCode
            record_validtime = rdata_mysql.recordValidTime
            # 如果不一致
            if code != record_code:
                return False, None
            elif datetime.datetime.now() > record_validtime:
                return True, 0
            else:
                return True, 1

    # 根据传入的关键操作别名，查询对应的操作标识符
    # 只查询mysql
    # 返回信息，第一位为有效位：
    # return {
    #     "exist": True,
    #     "operationid": operationid,
    # }
    # return {
    #     "exist": False,
    #     "operationid": None,
    # }
    # return {
    #     "exist": None,
    #     "operationid": None,
    # }
    @classmethod
    def check_operate(cls, alias):
        data = {
            "exist": None,
            "operationId": None,
        }
        # 查询关键操作唯一标识符
        try:
            odata = model_mysql_operationinfo.query.filter_by(
                operationAlias=alias
            ).first()
        except Exception as e:
            logmsg = "操作查询失败，失败原因：" + repr(e)
            api_logger.debug(logmsg)
            return data
        if odata is None:
            data["exist"] = False
            return data
        else:
            data["exist"] = True
            data["operationId"] = odata.operationId
            return data

    # 根据传入的账户邮箱以及token值，返回token是否有效
    # 只查询redis
    # 返回信息，第一位为有效位：
    # return {
    #     "exist": True,
    #     "valid": Ture,
    # }
    # return {
    #     "exist": True,
    #     "valid": False,
    # }
    # return {
    #     "exist": False,
    #     "valid": None,
    # }
    # return {
    #     "exist": False,
    #     "valid": None,
    # }
    @classmethod
    def check_token(cls, mail, token):
        data = {
            "exist": None,
            "valid": None,
        }
        # 查询关键操作唯一标识符
        try:
            tdata = model_redis_usertoken.query(mail)
        except Exception as e:
            logmsg = "操作查询失败，失败原因：" + repr(e)
            api_logger.debug(logmsg)
            return data
        if tdata is None:
            data["exist"] = False
            return data
        else:
            # 格式化缓存基础信息内容
            try:
                t = json.loads(tdata.decode("utf8"))
                logmsg = "缓存中账户token信息json格式化成功"
                api_logger.debug(logmsg)
                data["exist"] = True
            except Exception as e:
                logmsg = "缓存中账户token信息json格式化失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                for d in data:
                    data[d] = None
                return data
            # 判断是否一致且有效
            if token != t["userToken"]:
                data["valid"] = False
                return data
            elif datetime.datetime.strptime(t["validTime"], "%Y-%m-%d %H:%M:%S") > datetime.datetime.now():
                data["valid"] = True
                return data
            else:
                data["valid"] = False
                return data

    """ 
        根据传入的功能id以及功能父级id，返回功能是否存在
        用以检查permission数据是否有效
        只查询mysql
        返回信息，第一位为有效位：
        return {
            "exist": True
        }
        return {
            "exist": False
        }
        return {
            "exist": None
        }
    """
    @classmethod
    def check_function(cls, functionid, rootid):
        data = {
            "exist": None
        }

        try:
            data_mysql = model_mysql_functioninfo.query.filter_by(
                functionId=functionid,
                rootId=rootid
            ).first()
        except Exception as e:
            logmsg = "数据库中角色权限数据校验失败，失败原因：" + repr(e)
            api_logger.error(logmsg)
        else:
            logmsg = "数据库中角色权限数据校验成功"
            api_logger.debug(logmsg)
            if data_mysql is None:
                data["exist"] = False
            else:
                data["exist"] = True
        return data

    """
        根据传入的角色id以及api地址，判断角色是否具有api访问权限
        查询redis，若无角色id对应记录则查询mysql
        如果redis中有角色id的数据，但是没有apiurl的数据，则直接通过
        返回信息，第一位为有效位，告知角色是否存在：
        return {
            "exist": True,
            "pass": True
        }
        return {
            "exist": False,
            "pass": None
        }
        return {
            "exist": None
            "pass": None
        }
    """
    @classmethod
    def check_auth(cls, roleid, apiurl):
        data = {
            "exist": None,
            "pass": None,
        }
        # 查询关键操作唯一标识符
        try:
            adata = model_redis_apiauth.query(roleid)
        except Exception as e:
            logmsg = "操作查询失败，失败原因：" + repr(e)
            api_logger.debug(logmsg)
            return data
        # 如果缓存中查询到了
        if adata is not None:
            data["exist"] = True
            # 格式化缓存基础信息内容
            try:
                a = json.loads(adata.decode("utf8"))
                logmsg = "缓存中角色后端权限信息json格式化成功"
                api_logger.debug(logmsg)
            except Exception as e:
                logmsg = "缓存中角色后端权限信息json格式化失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
                for d in data:
                    data[d] = None
                return data
            else:
                # 判断url是否存在
                if apiurl in a:
                    # 存在
                    # 为1则返回通过，否则不通过
                    data["pass"] = True if a[apiurl] == 1 else False
                    return data
                else:
                    # 不存在，不作鉴权
                    data["pass"] = True
                    return data
        # 如果缓存中未查询到
        else:
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
                    model_mysql_rolepermission.roleId == roleid
                ).all()
                logmsg = "数据库中角色权限配置信息读取成功"
                api_logger.debug(logmsg)
            except Exception as e:
                logmsg = "数据库中角色权限配置信息读取失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
            else:
                # 如果mysql中未查询到
                if not role_api_auth_data:
                    # 返回
                    data["exist"] = False
                    return data
                # 如果mysql中查询到了
                else:
                    data["exist"] = True
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
                            roleid,
                            json.dumps(auth)
                        )
                    except Exception as e:
                        logmsg = "缓存库中角色权限信息写入失败，失败原因：" + repr(e)
                        api_logger.error(logmsg)

                    # 判断url是否存在
                    if apiurl in auth:
                        # 存在
                        # 为1则返回通过，否则不通过
                        data["pass"] = True if auth[apiurl] == 1 else False
                        return data
                    else:
                        # 不存在，不作鉴权
                        data["pass"] = True
                        return data
