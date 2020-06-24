# -*- coding: utf-8 -*-

import json
import datetime

from handler.log import api_logger
from handler.pool import mysqlpool

from model.redis import model_redis_usertoken
from model.redis import model_redis_apiauth

from model.mysql import model_mysql_userinfo
from model.mysql import model_mysql_rolepermission
from model.mysql import model_mysql_apiinfo
from model.mysql import model_mysql_functionorg


# 201请求错误/301传参非法/500系统异常
error_msgs = {
    'msg_no_user': json.dumps({"error_code": 201, "error_msg": "账户不存在", "data": {}}),
    'msg_no_plan': json.dumps({"error_code": 201, "error_msg": "测试计划不存在", "data": {}}),
    'msg_no_test_task': json.dumps({"error_code": 201, "error_msg": "无测试任务", "data": {}}),
    'msg_no_assign': json.dumps({"error_code": 201, "error_msg": "无分配记录", "data": {}}),
    'msg_no_table': json.dumps({"error_code": 201, "error_msg": "测试计划工作台无内容", "data": {}}),
    'msg_too_early': json.dumps({"error_code": 201, "error_msg": "测试任务开始时间过早", "data": {}}),
    'msg_worker_not_exist': json.dumps({"error_code": 201, "error_msg": "worker不存在", "data": {}}),
    'msg_no_case': json.dumps({"error_code": 201, "error_msg": "测试用例不存在", "data": {}}),
    'msg_no_version': json.dumps({"error_code": 201, "error_msg": "未找到测试计划的版本", "data": {}}),
    'msg_no_plan_type': json.dumps({"error_code": 201, "error_msg": "测试计划类型不存在", "data": {}}),
    'msg_no_task': json.dumps({"error_code": 201, "error_msg": "任务不存在", "data": {}}),
    'msg_plan_notopen': json.dumps({"error_code": 201, "error_msg": "测试计划未开放", "data": {}}),
    'msg_data_error': json.dumps({"error_code": 201, "error_msg": "数据非法", "data": {}}),
    'msg_no_role_auth_data': json.dumps({"error_code": 201, "error_msg": "账户所属角色无权限数据", "data": {}}),
    'msg_be_forbidden': json.dumps({"error_code": 201, "error_msg": "账户已禁用", "data": {}}),
    'msg_no_auth': json.dumps({"error_code": 201, "error_msg": "账户无访问权限", "data": {}}),
    'msg_status_error': json.dumps({"error_code": 201, "error_msg": "账户状态异常", "data": {}}),
    'msg_need_register': json.dumps({"error_code": 201, "error_msg": "账户未激活", "data": {}}),
    'msg_before_login': json.dumps({"error_code": 201, "error_msg": "请先登录账号", "data": {}}),
    'msg_token_wrong': json.dumps({"error_code": 201, "error_msg": "Token校验失败", "data": {}}),
    'msg_token_expired': json.dumps({"error_code": 201, "error_msg": "Token过期", "data": {}}),
    'msg_request_body_not_json': json.dumps({"error_code": 301, "error_msg": "传参格式非法", "data": {}}),
    'msg_value_type_error': json.dumps({"error_code": 301, "error_msg": "传参格式非法", "data": {}}),
    'msg_lack_keys': json.dumps({"error_code": 302, "error_msg": "缺少必传参数", "data": {}}),
    'msg_json_format_fail': json.dumps({"error_code": 500, "error_msg": "缓存处理失败", "data": {}}),
    'msg_db_error': json.dumps({"error_code": 500, "error_msg": "数据查询失败", "data": {}}),
    'msg_tasktype_error': json.dumps({"error_code": 201, "error_msg": "调试任务不支持查看此报告", "data": {}}),
    'msg_plantype_error': json.dumps({"error_code": 201, "error_msg": "自动化功能测试任务不支持查看此报告", "data": {}}),
    'msg_no_worker': json.dumps({"error_code": 500, "error_msg": "当前无可用worker", "data": {}}),
    'msg_file_error': json.dumps({"error_code": 500, "error_msg": "文件操作失败", "data": {}}),
    'msg_deploy_failed': json.dumps({"error_code": 500, "error_msg": "测试任务下发失败，请尽快联系管理员", "data": {}})
}

"""
    校验账户令牌校验能否通过
    说明：
        若请求头内缺少关键参数，则直接返回False
        若请求头内的校验数据校验失败，则直接返回False
        若校验通过，则通过
    入参：
        mail--邮箱地址
        token--账户令牌
    返回：
        1.校验通过则返回True
        2.校验失败直接返回False
"""


def check_token(mail, token):
    # 去缓存的token中查询Mail，不存在的话即为从来没登陆过
    # redis查询无错误信息，不作try处理
    api_logger.debug("准备查询" + mail + "的缓存token数据")
    tdata = model_redis_usertoken.query(mail)
    if tdata is None:
        api_logger.debug(mail + "的缓存token数据为空")
        return False
    else:
        api_logger.debug(mail + "的缓存token数据存在")
        # 格式化缓存基础信息内容
        try:
            t = json.loads(tdata.decode("utf8"))
            api_logger.debug(mail + "的缓存token数据json格式化成功")
        except Exception as e:
            api_logger.error(mail + "的缓存token数据json格式化失败，失败原因：" + repr(e))
            return False
        # 判断是否一致且有效
        # 判断是否过期
        if token != t["userToken"]:
            return False
        elif datetime.datetime.strptime(t["validTime"], "%Y-%m-%d %H:%M:%S") < datetime.datetime.now():
            return False
    # 检查通过，返回True
    return True


"""
    校验账户是否存在以及账户当前状态
    说明：
        根据传入的邮件地址判断账户信息在redis以及mysql中是否存在
        如果在redis中查询成功，则通过
        如果在redis中未查询到，则查询mysql，将结果写入redis后通过
        如果在mysql中未查询到，则直接返回False
    入参：
        mail--邮箱地址
    返回：
        1.校验通过则返回True
        2.校验失败直接返回False
"""


def check_user(mail):
    api_logger.debug("准备查询" + mail + "的缓存账户数据")
    # 尝试从mysql中查询
    try:
        api_logger.debug("准备查询" + mail + "的账户数据")
        uinfo_mysql = model_mysql_userinfo.query.filter_by(userEmail=mail).first()
        api_logger.debug(mail + "的账户数据查询成功")
    except Exception as e:
        api_logger.error(mail + "的账户数据查询失败，失败原因：" + repr(e))
        return False
    else:
        # 如果mysql中未查询到
        if uinfo_mysql is None:
            return False
        # 如果mysql中查询到了
        else:
            # 判断账户状态
            if uinfo_mysql.userStatus == 0:
                return False
            elif uinfo_mysql.userStatus == -1:
                return False
            elif uinfo_mysql.userStatus != 1:
                return False
    return True


"""
    校验账户所属角色是否拥有API访问权限
    说明：
        根据传入的账户信息，读取到其所属角色，然后判断该角色是否拥有api访问权限
        若未查询到缓存的账号信息，则直接返回False。因为本方法一般用在check_user检查的后面，所以基本上不会出现该情况
        若账号所属角色为空，则直接返回False
        若账号所属角色在缓存的api权限数据中无访问权限，则直接返回False
        若账号所属角色的api权限数据无缓存，则尝试从mysql中同步，再进行判断
    入参：
        mail--邮箱地址
        url--访问地址
    返回：
        1.校验通过则返回True
        2.校验失败直接返回False
"""


def check_auth(user_id, url):
    # 取出账户所属roleId
    # 首先查询缓存中账户信息，尝试取出roleId
    api_logger.debug("准备查询缓存账户数据")
    # 首先查询账户信息，尝试取出roleId
    api_logger.debug("准备查询账户数据")
    try:
        api_logger.debug("准备查询账户数据")
        uinfo_mysql = model_mysql_userinfo.query.filter_by(userId=user_id).first()
        api_logger.debug("账户数据查询成功")
    except Exception as e:
        api_logger.error("账户数据查询失败，失败原因：" + repr(e))
        return error_msgs['msg_db_error']
    else:
        # 如果查询到了
        if uinfo_mysql is not None:
            api_logger.debug("账户数据存在")
            # 取出roleId
            role_id = uinfo_mysql.userRoleId
            # 如果role_id不为空
            if role_id is not None:
                # 根据roleId检查账户所属是否有api访问权限
                api_logger.debug("准备查询所属角色的缓存api访问权限数据")
                redis_apiauth = model_redis_apiauth.query(role_id)
                if redis_apiauth is not None:
                    # 格式化缓存api访问权限信息内容
                    try:
                        redis_apiauth_json = json.loads(redis_apiauth.decode("utf8"))
                        api_logger.debug("api访问权限数据json格式化成功")
                    except Exception as e:
                        api_logger.error("api访问权限数据json格式化失败，失败原因：" + repr(e))
                        return False
                    else:
                        if url in redis_apiauth_json and redis_apiauth_json[url] != 1:
                            return False
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
                            model_mysql_rolepermission.roleId == role_id
                        ).all()
                        api_logger.debug("数据库中角色权限配置信息读取成功")
                    except Exception as e:
                        api_logger.error("数据库中角色权限配置信息读取失败，失败原因：" + repr(e))

                    else:
                        # 如果mysql中未查询到
                        if not mysql_role_api_auth:
                            return False
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
                            model_redis_apiauth.set(role_id, json.dumps(auth))
                            """
                                判断url是否存在
                                如果存在，且不为1，则报错
                            """
                            if url in auth and auth[url] != 1:
                                return False
            # 如果role_id为空
            else:
                # 无角色，直接返回无权限
                return False
        else:
            # 无账号信息，直接返回无权限
            return False
    return True


"""
    校验必传项目
    说明：
        检查入参格式为可转成json格式的字符串
        校验必传参数，若存在未传的，返回false
        校验入参格式，若不符合类型要求以及长度要求，返回false
        
    入参：
        1.接受前端第一次请求的参数
        {"main":"xxx@fclassroom.com","token":"d6acecf0-e9bd-3951-a6c6-66e926b4dd7a","taskId":1}
        2.参数名称+要求数据类型+要求数据最小值(可为None，为None则无最小值)+要求数据最大值(可为None，为None则无最大值)组成的list，顺序不能错
        例：
        ['a', str, None, None]
        ['a', str, 1, 100]
        ['a', int, None, 100]
        ['a', int, 1, None]
        ['a', boolean]
        ['a', list, 0, None]
    返回：
        1.校验通过返回json参数
        2.校验失败返回false
"""


def check_parameter(action, *keys):
    if type(action) is str:
        try:
            api_logger.debug("准备检查参数格式")
            json_action = json.loads(action)
        except Exception as e:
            api_logger.warn("不能转为json格式，原因：" + repr(e))
            return False
        else:
            # 检查必传项目
            for key in keys:
                # 如果缺少必传项
                if key[0] not in json_action:
                    return False
                else:
                    value = json_action[key[0]]
                    # 先检查类型
                    if type(value) is not key[1]:
                        return False
                    # 如果非布尔型，则检查长度
                    if key[1] is not bool:
                        # 如果有最小值但没最大值
                        if key[2] and not key[3]:
                            if key[1] is str or key[1] is list:
                                # 如果比最小值还小
                                if len(value) < key[2]:
                                    return False
                            elif key[1] is int:
                                # 如果比最小值还小
                                if value < key[2]:
                                    return False
                        # 如果有最小以及最大值
                        elif key[2] and key[3]:
                            if key[1] is str or key[1] is list:
                                # 如果比最小值还小或者比最大值还大
                                if len(value) < key[2] or len(value) > key[3]:
                                    return False
                            elif key[1] is int:
                                # 如果比最小值还小或者比最大值还大
                                if value < key[2] or value > key[3]:
                                    return False
                        # 如果有没有最小值但有最大值
                        elif not key[2] and key[3]:
                            if key[1] is str or key[1] is list:
                                # 如果比最大值还大
                                if len(value) > key[3]:
                                    return False
                            elif key[1] is int:
                                # 如果比最大值还大
                                if value > key[3]:
                                    return False
            return json_action
    else:
        return False
