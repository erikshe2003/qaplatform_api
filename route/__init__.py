# -*- coding: utf-8 -*-

import flask
import json
import os
import datetime
import uuid

from functools import wraps

from handler.log import api_logger
from handler.pool import mysqlpool

from model.redis import model_redis_usertoken
from model.redis import model_redis_apiauth
from model.redis import model_redis_rolepermission

from model.mysql import model_mysql_userinfo
from model.mysql import model_mysql_rolepermission
from model.mysql import model_mysql_apiinfo
from model.mysql import model_mysql_functioninfo
from model.mysql import model_mysql_functionorg




# 201请求错误/301传参非法/500系统异常
error_msgs = {
    201: {

        'msg_no_projectmember': {"error_code": 201, "error_msg": "项目成员不存在", "data": {}},
        'msg_no_project': {"error_code": 201, "error_msg": "项目不存在", "data": {}},
        'msg_exit_project': {"error_code": 201, "error_msg": "项目已存在", "data": {}},
        'msg_exit_depository': {"error_code": 201, "error_msg": "仓库已存在", "data": {}},
        'msg_no_depository': {"error_code": 201, "error_msg": "仓库不存在", "data": {}},
        'msg_exit_catalogue': {"error_code": 201, "error_msg": "目录已存在", "data": {}},
        'msg_no_catalogue': {"error_code": 201, "error_msg": "目录不存在", "data": {}},
        'msg_exit_subject': {"error_code": 201, "error_msg": "项目已存在", "data": {}},
        'msg_no_subject': {"error_code": 201, "error_msg": "项目不存在", "data": {}},
        'action_code_non': {"error_code": 201, "error_msg": "操作码不存在", "data": {}},
        'action_code_expire': {"error_code": 201, "error_msg": "操作码已过期", "data": {}},
        'action_code_error': {"error_code": 201, "error_msg": "操作码异常", "data": {}},
        'msg_before_login': {"error_code": 201, "error_msg": "请先登录账号", "data": {}},
        'msg_data_error': {"error_code": 201, "error_msg": "数据非法", "data": {}},
        'msg_illegal_format': {"error_code": 201, "error_msg": "数据格式非法", "data": {}},
        'msg_mail_exist': {"error_code": 201, "error_msg": "邮箱已被注册", "data": {}},
        'msg_new_password_inconformity': {"error_code": 201, "error_msg": "两次密码不一致", "data": {}},
        'msg_need_register': {"error_code": 201, "error_msg": "账户未激活", "data": {}},
        'msg_no_user': {"error_code": 201, "error_msg": "账户不存在", "data": {}},
        'msg_no_role': {"error_code": 201, "error_msg": "角色不存在", "data": {}},
        'msg_no_plan': {"error_code": 201, "error_msg": "测试计划不存在", "data": {}},
        'msg_no_test_task': {"error_code": 201, "error_msg": "无测试任务", "data": {}},
        'msg_no_assign': {"error_code": 201, "error_msg": "无分配记录", "data": {}},
        'msg_no_table': {"error_code": 201, "error_msg": "测试计划工作台无内容", "data": {}},
        'msg_no_case': {"error_code": 201, "error_msg": "测试用例不存在", "data": {}},
        'msg_no_version': {"error_code": 201, "error_msg": "未找到测试计划的版本", "data": {}},
        'msg_no_data': {"error_code": 201, "error_msg": "缺少快照数据", "data": {}},
        'msg_no_plan_type': {"error_code": 201, "error_msg": "测试计划类型不存在", "data": {}},
        'msg_no_role_auth_data': {"error_code": 201, "error_msg": "账户所属角色无权限数据", "data": {}},
        'msg_no_task': {"error_code": 201, "error_msg": "任务不存在", "data": {}},
        'msg_no_auth': {"error_code": 201, "error_msg": "账户无访问权限", "data": {}},
        'msg_not_temporary': {"error_code": 201, "error_msg": "非临时版本", "data": {}},
        'msg_old_password_incorrect': {"error_code": 201, "error_msg": "旧密码输入错误", "data": {}},
        'msg_plan_notopen': {"error_code": 201, "error_msg": "测试计划未开放", "data": {}},
        'msg_plan_user_error': {"error_code": 201, "error_msg": "您不是这个测试计划的所有者", "data": {}},
        'msg_plantype_error': {"error_code": 201, "error_msg": "自动化功能测试任务不支持查看此报告", "data": {}},
        'msg_request_file_oversize': {"error_code": 201, "error_msg": "文件大小超出规定", "data": {}},
        'msg_role_is_admin': {"error_code": 201, "error_msg": "管理员角色禁止操作", "data": {}},
        'msg_status_error': {"error_code": 201, "error_msg": "账户状态异常", "data": {}},
        'msg_too_early': {"error_code": 201, "error_msg": "测试任务开始时间不能小于当前时间", "data": {}},
        'msg_tasktype_error': {"error_code": 201, "error_msg": "调试任务不支持查看此报告", "data": {}},
        'msg_task_time_error': {"error_code": 201, "error_msg": "测试任务结束时间不能小于开始时间且相隔不能小于10s", "data": {}},
        'msg_user_is_admin': {"error_code": 201, "error_msg": "管理员账号禁止操作", "data": {}},
        'msg_user_id_wrong': {"error_code": 201, "error_msg": "账号数据错误", "data": {}},
        'msg_user_forbidden': {"error_code": 201, "error_msg": "账号已禁用", "data": {}},
        'msg_user_exist': {"error_code": 201, "error_msg": "登录名已被注册", "data": {}},
        'msg_user_cannot_operate': {"error_code": 201, "error_msg": "用户账号禁止操作", "data": {}},
        'msg_worker_not_exist': {"error_code": 201, "error_msg": "worker不存在", "data": {}}
    },
    301: {
        'msg_request_params_illegal': {"error_code": 301, "error_msg": "传参格式非法", "data": {}},
        'msg_request_body_not_json': {"error_code": 301, "error_msg": "传参格式非法", "data": {}},
        'msg_request_body_not_url_args': {"error_code": 301, "error_msg": "传参格式非法", "data": {}},
        'msg_value_type_error': {"error_code": 301, "error_msg": "传参格式非法", "data": {}}
    },
    302: {
        'msg_request_params_incomplete': {"error_code": 302, "error_msg": "缺少必传参数", "data": {}}
    },
    401: {
        'msg_token_wrong': {"error_code": 401, "error_msg": "Token校验失败", "data": {}},
        'msg_token_expired': {"error_code": 401, "error_msg": "Token过期", "data": {}}
    },
    500: {
        'msg_server_error': {"error_code": 500, "error_msg": "服务异常", "data": {}},
        'msg_db_error': {"error_code": 500, "error_msg": "数据查询失败", "data": {}},
        'msg_redis_error': {"error_code": 500, "error_msg": "缓存处理失败", "data": {}},
        'msg_db_update_error': {"error_code": 500, "error_msg": "数据更新失败", "data": {}},
        'msg_json_format_fail': {"error_code": 500, "error_msg": "缓存处理失败", "data": {}},
        'msg_no_worker': {"error_code": 500, "error_msg": "当前无可用worker", "data": {}},
        'msg_file_error': {"error_code": 500, "error_msg": "文件操作失败", "data": {}},
        'msg_deploy_failed': {"error_code": 500, "error_msg": "测试任务下发失败，请尽快联系管理员", "data": {}}
    }
}


# 刷新redis缓存
# apiAuth
def refresh_redis_apiauth(role_id):
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
            model_mysql_rolepermission.roleId == role_id
        ).all()
        logmsg = "数据库中角色权限信息修改后页面权限配置信息读取成功"
        api_logger.debug(logmsg)
    except Exception as e:
        logmsg = "数据库中角色权限信息修改后页面权限配置信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
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
                role_id,
                json.dumps(auth)
            )
        except Exception as e:
            logmsg = "缓存库中角色权限信息写入失败，失败原因：" + repr(e)
            api_logger.error(logmsg)


# rolePermission
def refresh_redis_rolepermission(role_id):
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
            model_mysql_rolepermission.roleId == role_id,
            model_mysql_functioninfo.functionType == 1,
            model_mysql_rolepermission.hasPermission == 1
        ).all()
        logmsg = "数据库中角色权限信息修改后页面权限配置信息读取成功"
        api_logger.debug(logmsg)
    except Exception as e:
        logmsg = "数据库中角色权限信息修改后页面权限配置信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
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
                    model_mysql_rolepermission.roleId == role_id,
                    model_mysql_functioninfo.rootId == page_permission.functionId,
                    model_mysql_functioninfo.functionType == 2,
                    model_mysql_rolepermission.hasPermission == 1
                ).all()
                logmsg = "数据库中角色权限信息修改后功能权限配置信息读取成功"
                api_logger.debug(logmsg)
            except Exception as e:
                logmsg = "数据库中角色权限信息修改后功能权限配置信息读取失败，失败原因：" + repr(e)
                api_logger.error(logmsg)
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
                role_id,
                json.dumps(permission)
            )
        except Exception as e:
            logmsg = "缓存库中角色权限信息写入失败，失败原因：" + repr(e)
            api_logger.error(logmsg)


# userToken
def refresh_redis_usertoken(user_id, remember):
    user_token = str(
        uuid.uuid3(
            uuid.NAMESPACE_DNS, str(user_id) + str(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        )
    )

    if remember is True:
        t = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        t = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    model_redis_usertoken.set(
        user_id,
        "{\"userToken\":\"" + user_token + "\"," +
        "\"validTime\":\"" + t +
        "\"}"
    )

    return user_token


"""
    装饰器-校验请求头是否包含MAIL和TOKEN，以及账户令牌校验能否通过
    说明：
        若请求头内缺少关键参数，则直接返回http错误响应
        若请求头内的校验数据校验失败，则直接返回http错误响应
        若校验通过，则通过
    入参：
        无
    返回：
        1.校验通过则执行应用逻辑
        2.校验失败直接返回http错误响应
"""


def check_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 首先检查必传参数Mail/Token
        if 'UserId' not in flask.request.headers or 'Token' not in flask.request.headers:
            return error_msgs[302]['msg_request_params_incomplete']
        user_id = flask.request.headers['UserId']
        user_token = flask.request.headers['Token']
        # 然后检查token是否正确
        # 去缓存的token中查询Mail，不存在的话即为从来没登陆过
        # redis查询无错误信息，不作try处理
        api_logger.debug("准备查询缓存token数据")
        tdata = model_redis_usertoken.query(user_id)
        if tdata is None:
            api_logger.debug("缓存token数据为空")
            return error_msgs[201]['msg_before_login']
        else:
            api_logger.debug("缓存token数据存在")
            # 格式化缓存基础信息内容
            try:
                t = json.loads(tdata.decode("utf8"))
                api_logger.debug("缓存token数据json格式化成功")
            except Exception as e:
                api_logger.error("缓存token数据json格式化失败，失败原因：" + repr(e))
                return error_msgs[500]['msg_json_format_fail']
            # 判断是否一致且有效
            # 判断是否过期
            if user_token != t["userToken"]:
                return error_msgs[401]['msg_token_wrong']
            elif datetime.datetime.strptime(t["validTime"], "%Y-%m-%d %H:%M:%S") < datetime.datetime.now():
                return error_msgs[401]['msg_token_expired']
        # 检查通过，执行应用逻辑
        return func(*args, **kwargs)
    return wrapper


"""
    装饰器-校验账户是否存在以及账户当前状态
    说明：
        根据传入的邮件地址判断账户信息在redis以及mysql中是否存在
        如果在redis中查询成功，则通过
        如果在redis中未查询到，则查询mysql，将结果写入redis后通过
        如果在mysql中未查询到，则直接返回http错误响应
    入参：
        无
    返回：
        1.校验通过则执行应用逻辑
        2.校验失败直接返回http错误响应
"""


def check_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 首先检查必传参数Mail/Token
        if 'UserId' not in flask.request.headers:
            return error_msgs[302]['msg_request_params_incomplete']
        user_id = flask.request.headers['UserId']
        # 尝试从mysql中查询
        try:
            api_logger.debug("准备查询账户数据")
            uinfo_mysql = model_mysql_userinfo.query.filter_by(userId=user_id).first()
            api_logger.debug("账户数据查询成功")
        except Exception as e:
            api_logger.error("账户数据查询失败，失败原因：" + repr(e))
            return error_msgs[500]['msg_db_error']
        else:
            # 如果mysql中未查询到
            if uinfo_mysql is None:
                return error_msgs[201]['msg_no_user']
            # 如果mysql中查询到了
            else:
                # 判断账户状态
                if uinfo_mysql.userStatus == 0:
                    return error_msgs[201]['msg_need_register']
                elif uinfo_mysql.userStatus == -1:
                    return error_msgs[201]['msg_user_forbidden']
                elif uinfo_mysql.userStatus != 1:
                    return error_msgs[201]['msg_status_error']
        # 检查通过，执行应用逻辑
        return func(*args, **kwargs)
    return wrapper


"""
    装饰器-校验账户所属角色是否拥有API访问权限
    说明：
        根据传入的账户信息，读取到其所属角色，然后判断该角色是否拥有api访问权限
        若未查询到缓存的账号信息，则直接返回http错误响应。因为本装饰器一般用在check_user装饰器的后面，所以基本上不会出现该情况
        若账号所属角色为空，则直接返回http错误响应
        若账号所属角色在缓存的api权限数据中无访问权限，则直接返回http错误响应
        若账号所属角色的api权限数据无缓存，则尝试从mysql中同步，再进行判断
    入参：
        无
    返回：
        1.校验通过则执行应用逻辑
        2.校验失败直接返回http错误响应
"""


def check_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 首先检查必传参数Mail/Token
        if 'UserId' not in flask.request.headers:
            return error_msgs[302]['msg_request_params_incomplete']
        user_id = flask.request.headers['UserId']
        api_url = flask.request.url
        # 取出账户所属roleId
        # 首先查询账户信息，尝试取出roleId
        api_logger.debug("准备查询账户数据")
        try:
            api_logger.debug("准备查询账户数据")
            uinfo_mysql = model_mysql_userinfo.query.filter_by(userId=user_id).first()
            api_logger.debug("账户数据查询成功")
        except Exception as e:
            api_logger.error("账户数据查询失败，失败原因：" + repr(e))
            return error_msgs[500]['msg_db_error']
        else:
            # 如果mysql中查询到了
            if uinfo_mysql is not None:
                # 尝试去redis中查询缓存的auth数据
                # 根据roleId检查账户所属是否有api访问权限
                api_logger.debug("准备查询所属角色的缓存api访问权限数据")
                redis_apiauth = model_redis_apiauth.query(uinfo_mysql.userRoleId)
                if redis_apiauth is not None:
                    # 格式化缓存api访问权限信息内容
                    try:
                        redis_apiauth_json = json.loads(redis_apiauth.decode("utf8"))
                        api_logger.debug("缓存api访问权限数据json格式化成功")
                    except Exception as e:
                        api_logger.error("缓存api访问权限数据json格式化失败，失败原因：" + repr(e))
                        return error_msgs[500]['msg_db_error']
                    else:
                        if api_url.split('/')[-1] in redis_apiauth_json and redis_apiauth_json[api_url.split(
                                '/')[-1]] != 1:
                            return error_msgs[201]['msg_no_auth']
                # 如果redis中未查询到
                else:
                    # 尝试去mysql中查询最新的角色权限配置数据
                    try:
                        api_logger.debug("准备查询所属角色的api访问权限数据")
                        mysql_role_api_auth = mysqlpool.session.query(
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
                            model_mysql_rolepermission.roleId == uinfo_mysql.userRoleId
                        ).all()
                        api_logger.debug("数据库中角色权限配置信息读取成功")
                    except Exception as e:
                        api_logger.error("数据库中角色权限配置信息读取失败，失败原因：" + repr(e))
                    else:
                        # 如果mysql中未查询到
                        if not mysql_role_api_auth:
                            return error_msgs[201]['msg_no_role_auth_data']
                        # 如果mysql中查询到了
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
                            for auth_data in mysql_role_api_auth:
                                auth[auth_data.apiUrl] = auth_data.hasPermission
                            """
                                然后将需缓存的内容缓存至redis的apiAuth
                                需缓存内容:
                                key=roleId
                                value=auth
                            """
                            model_redis_apiauth.set(uinfo_mysql.userRoleId, json.dumps(auth))
                            """
                                判断url是否存在
                                如果存在，且不为1，则报错
                            """
                            if api_url in auth and auth[api_url] != 1:
                                return error_msgs[201]['msg_no_auth']
            # 如果role_id为空
            elif uinfo_mysql.userRoleId is None:
                # 无角色，直接返回无权限
                return error_msgs[201]['msg_no_auth']
            else:
                # 无账号信息，直接返回无权限
                return error_msgs[201]['msg_no_auth']
        # 检查账户所属角色的权限清单
        return func(*args, **kwargs)
    return wrapper


"""
    装饰器-校验GET请求必传项目
    说明：
        检查入参格式是否为json字符串，header中是否有Content-Type:application/json
        校验必传参数，若存在未传的，直接返回http错误响应
        校验入参格式，若不符合类型要求以及长度要求，直接返回http错误响应
    入参：
        1.参数名称+要求数据类型+要求数据最小值(可为None，为None则无最小值)+要求数据最大值(可为None，为None则无最大值)组成的list，顺序不能错
        例：
        ['a', str, None, None]
        ['a', str, 1, 100]
        ['a', int, None, 100]
        ['a', int, 1, None]
        ['a', boolean]
        ['a', list, 0, None]
    返回：
        1.校验通过则执行应用逻辑
        2.校验失败直接返回http错误响应
"""


def check_get_parameter(*keys):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if flask.request.method == "GET":
                request_url = flask.request.url
                api_logger.debug("URL:" + request_url + "准备检查请求格式")
                try:
                    request_parameters = flask.request.args
                except Exception as e:
                    api_logger.error("URL:" + request_url + "格式检查失败，原因：" + repr(e))
                    return error_msgs[301]['msg_request_body_not_json']
                else:
                    if not request_parameters:
                        return error_msgs[301]['msg_request_body_not_url_args']
                # 检查必传项目
                for key in keys:
                    # 1.检查有无
                    # 如果缺少必传项
                    if key[0] not in request_parameters:
                        return error_msgs[302]['msg_request_params_incomplete']
                    else:
                        value = request_parameters[key[0]]
                        # 对于get请求，传入的参数默认都是字符串
                        # 2.检查类型，并同时检查大小或者长度
                        # 根据参数检查要求，尝试进行转换
                        if key[1] is int:
                            # 类型
                            try:
                                ivalue = int(value)
                            except Exception as e:
                                api_logger.debug("URL:" + request_url + "格式检查失败，原因：" + repr(e))
                                return error_msgs[301]['msg_value_type_error']
                            else:
                                # 大小
                                # 如果有最小值和最大值
                                if key[2] and key[3]:
                                    if ivalue > key[3] or ivalue < key[2]:
                                        api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s不在区间范围内" % key[0])
                                        return error_msgs[301]['msg_value_type_error']
                                # 如果只有最小值
                                elif key[2]:
                                    if ivalue < key[2]:
                                        api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s小于最小值" % key[0])
                                        return error_msgs[301]['msg_value_type_error']
                                # 如果只有最大值
                                elif key[3]:
                                    if ivalue > key[3]:
                                        api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s超出最大值" % key[0])
                                        return error_msgs[301]['msg_value_type_error']
                        elif key[1] is str:
                            # 大小
                            # 如果有最小值和最大值
                            if key[2] and key[3]:
                                if len(value) > key[3] or len(value) < key[2]:
                                    api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s不在区间范围内" % key[0])
                                    return error_msgs[301]['msg_value_type_error']
                            # 如果只有最小值
                            elif key[2]:
                                if len(value) < key[2]:
                                    api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s小于最小值" % key[0])
                                    return error_msgs[301]['msg_value_type_error']
                            # 如果只有最大值
                            elif key[3]:
                                if len(value) > key[3]:
                                    api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s超出最大值" % key[0])
                                    return error_msgs[301]['msg_value_type_error']
            return func(*args, **kwargs)
        return wrapper
    return decorator


"""
    装饰器-校验一般POST请求必传项目
    说明：
        检查入参格式是否为json字符串，header中是否有Content-Type:application/json
        校验必传参数，若存在未传的，直接返回http错误响应
        校验入参格式，若不符合类型要求以及长度要求，直接返回http错误响应
    入参：
        1.参数名称+要求数据类型+要求数据最小值(可为None，为None则无最小值)+要求数据最大值(可为None，为None则无最大值)组成的list，顺序不能错
        例：
        ['a', str, None, None]
        ['a', str, 1, 100]
        ['a', int, None, 100]
        ['a', int, 1, None]
        ['a', boolean]
        ['a', list, 0, None]
    返回：
        1.校验通过则执行应用逻辑
        2.校验失败直接返回http错误响应
"""


def check_post_parameter(*keys):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request_url = flask.request.url
            api_logger.debug("URL:" + request_url + ".准备检查请求格式")
            try:
                request_parameters = flask.request.json
            except Exception as e:
                api_logger.error("URL:" + request_url + "格式检查失败，原因：" + repr(e))
                return error_msgs[301]['msg_request_body_not_json']
            else:
                if not request_parameters:
                    return error_msgs[301]['msg_request_body_not_json']
            # 检查必传项目
            for key in keys:
                # 如果缺少必传项
                if key[0] not in request_parameters:
                    return error_msgs[302]['msg_request_params_incomplete']
                else:
                    value = request_parameters[key[0]]
                    # 先检查类型
                    if type(value) is not key[1]:
                        return error_msgs[301]['msg_value_type_error']
                    # 如果非布尔型，则检查长度
                    if key[1] is not bool:
                        # 如果有最小值但没最大值
                        if key[2] and not key[3]:
                            if key[1] is str or key[1] is list:
                                # 如果比最小值还小
                                if len(value) < key[2]:
                                    return error_msgs[301]['msg_value_type_error']
                            elif key[1] is int:
                                # 如果比最小值还小
                                if value < key[2]:
                                    return error_msgs[301]['msg_value_type_error']
                        # 如果有最小以及最大值
                        elif key[2] and key[3]:
                            if key[1] is str or key[1] is list:
                                # 如果比最小值还小或者比最大值还大
                                if len(value) < key[2] or len(value) > key[3]:
                                    return error_msgs[301]['msg_value_type_error']
                            elif key[1] is int:
                                # 如果比最小值还小或者比最大值还大
                                if value < key[2] or value > key[3]:
                                    return error_msgs[301]['msg_value_type_error']
                        # 如果有没有最小值但有最大值
                        elif not key[2] and key[3]:
                            if key[1] is str or key[1] is list:
                                # 如果比最大值还大
                                if len(value) > key[3]:
                                    return error_msgs[301]['msg_value_type_error']
                            elif key[1] is int:
                                # 如果比最大值还大
                                if value > key[3]:
                                    return error_msgs[301]['msg_value_type_error']
            return func(*args, **kwargs)
        return wrapper
    return decorator


"""
    装饰器-校验POST(form-data)请求必传项目
    说明：
        form类型的入参内容都是字符串
        检查header中是否有Content-Type:multipart/form-data
        校验必传参数，若存在未传的，直接返回http错误响应
        校验入参格式，若不符合类型要求以及长度要求，直接返回http错误响应
    入参：
        1.files
        
        2.forms
        参数名称+要求数据类型+要求数据最小值(可为None，为None则无最小值)+要求数据最大值(可为None，为None则无最大值)组成的list，顺序不能错
        例：
        ['a', str, None, None]
        ['a', str, 1, 100]
        ['a', int, None, 100]
        ['a', int, 1, None]
        ['a', boolean]
        ['a', list, 0, None]
    返回：
        1.校验通过则执行应用逻辑
        2.校验失败直接返回http错误响应
"""


def check_form_parameter(*keys):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if flask.request.method == "POST":
                # 检查files
                api_logger.debug("准备检查请求内的文件清单")
                try:
                    request_files = flask.request.files
                except Exception as e:
                    api_logger.warn("文件清单检查失败，原因：" + repr(e))
                    return error_msgs[301]['msg_request_params_illegal']
                else:
                    if not request_files:
                        return error_msgs[301]['msg_request_params_illegal']
                    else:
                        # 检查必传项目
                        check_files = keys[0]['files']
                        for check_file in check_files:
                            # 如果缺少必传项
                            if check_file[0] not in request_files:
                                return error_msgs[302]['msg_request_params_incomplete']
                            else:
                                request_file = request_files[check_file[0]]
                                request_file.seek(0, os.SEEK_END)
                                request_file_size = request_file.tell()
                                # 检查大小
                                if request_file_size < check_file[2] or request_file_size > check_file[3]:
                                    return error_msgs[201]['msg_request_file_oversize']
                                request_file.seek(0, 0)
                # 检查forms
                api_logger.debug("准备检查请求内的参数")
                try:
                    request_forms = flask.request.form
                except Exception as e:
                    api_logger.warn("请求内的参数检查失败，原因：" + repr(e))
                    return error_msgs[301]['msg_request_params_illegal']
                else:
                    if not request_forms:
                        return error_msgs[301]['msg_request_params_illegal']
                    else:
                        # 检查必传项目
                        check_forms = keys[0]['forms']
                        for check_form in check_forms:
                            # 如果缺少必传项
                            if check_form[0] not in request_forms:
                                return error_msgs[302]['msg_request_params_incomplete']
                            else:
                                request_form = request_forms[check_form[0]]
                                # 先检查类型
                                # 由于form类型的值传递时实际都为字符串，故要先尝试转换
                                try:
                                    request_form_trans = check_form[1](request_form)
                                except Exception as e:
                                    api_logger.warn("表单数据转换失败，原因：" + repr(e))
                                    return error_msgs[301]['msg_request_params_illegal']
                                else:
                                    check_flag = True
                                    # 如果bool
                                    # 不检查
                                    if check_form[1] is bool:
                                        pass
                                    # 如果int
                                    if check_form[1] is int:
                                        # 如果有最小值限定
                                        if check_form[2] and request_form_trans < check_form[2]:
                                            check_flag = False
                                        # 如果有最大值限定
                                        if check_form[3] and request_form_trans > check_form[3]:
                                            check_flag = False
                                        # 判断失败
                                        if not check_flag:
                                            return error_msgs[301]['msg_request_params_illegal']
                                    # 如果str
                                    if check_form[1] is str:
                                        # 如果有最小值限定
                                        if check_form[2] and len(request_form_trans) < check_form[2]:
                                            check_flag = False
                                        # 如果有最大值限定
                                        if check_form[3] and len(request_form_trans) > check_form[3]:
                                            check_flag = False
                                        # 判断失败
                                        if not check_flag:
                                            return error_msgs[301]['msg_request_params_illegal']
            return func(*args, **kwargs)
        return wrapper
    return decorator


"""
    装饰器-校验DELETE请求必传项目
    说明：
        校验必传参数，若存在未传的，直接返回http错误响应
        校验入参格式，若不符合类型要求以及长度要求，直接返回http错误响应
    入参：
        1.参数名称+要求数据类型+要求数据最小值(可为None，为None则无最小值)+要求数据最大值(可为None，为None则无最大值)组成的list，顺序不能错
        例：
        ['a', str, None, None]
        ['a', str, 1, 100]
        ['a', int, None, 100]
        ['a', int, 1, None]
        ['a', boolean]
        ['a', list, 0, None]
    返回：
        1.校验通过则执行应用逻辑
        2.校验失败直接返回http错误响应
"""


def check_delete_parameter(*keys):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if flask.request.method == "DELETE":
                request_url = flask.request.url
                api_logger.debug("URL:" + request_url + "准备检查请求格式")
                try:
                    request_parameters = flask.request.args
                except Exception as e:
                    api_logger.error("URL:" + request_url + "格式检查失败，原因：" + repr(e))
                    return error_msgs[301]['msg_request_body_not_json']
                else:
                    if not request_parameters:
                        return error_msgs[301]['msg_request_body_not_url_args']
                # 检查必传项目
                for key in keys:
                    # 1.检查有无
                    # 如果缺少必传项
                    if key[0] not in request_parameters:
                        return error_msgs[302]['msg_request_params_incomplete']
                    else:
                        value = request_parameters[key[0]]
                        # 对于get请求，传入的参数默认都是字符串
                        # 2.检查类型，并同时检查大小或者长度
                        # 根据参数检查要求，尝试进行转换
                        if key[1] is int:
                            # 类型
                            try:
                                ivalue = int(value)
                            except Exception as e:
                                api_logger.debug("URL:" + request_url + "格式检查失败，原因：" + repr(e))
                                return error_msgs[301]['msg_value_type_error']
                            else:
                                # 大小
                                # 如果有最小值和最大值
                                if key[2] and key[3]:
                                    if ivalue > key[3] or ivalue < key[2]:
                                        api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s不在区间范围内" % key[0])
                                        return error_msgs[301]['msg_value_type_error']
                                # 如果只有最小值
                                elif key[2]:
                                    if ivalue < key[2]:
                                        api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s小于最小值" % key[0])
                                        return error_msgs[301]['msg_value_type_error']
                                # 如果只有最大值
                                elif key[3]:
                                    if ivalue > key[3]:
                                        api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s超出最大值" % key[0])
                                        return error_msgs[301]['msg_value_type_error']
                        elif key[1] is str:
                            # 大小
                            # 如果有最小值和最大值
                            if key[2] and key[3]:
                                if len(value) > key[3] or len(value) < key[2]:
                                    api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s不在区间范围内" % key[0])
                                    return error_msgs[301]['msg_value_type_error']
                            # 如果只有最小值
                            elif key[2]:
                                if len(value) < key[2]:
                                    api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s小于最小值" % key[0])
                                    return error_msgs[301]['msg_value_type_error']
                            # 如果只有最大值
                            elif key[3]:
                                if len(value) > key[3]:
                                    api_logger.debug("URL:" + request_url + "格式检查失败，原因：参数%s超出最大值" % key[0])
                                    return error_msgs[301]['msg_value_type_error']
            return func(*args, **kwargs)
        return wrapper
    return decorator
