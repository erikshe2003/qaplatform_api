# -*- coding: utf-8 -*-

import os
import flask
import json
import route

from handler.log import api_logger
from handler.config import appconfig

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_userinfo

"""
    上传接口测试计划内参数化插件所用到的文件-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断文件大小
            判断插件是否支持该文件类型
            判断计划拥有者是否为本人
            尝试将文件存储至服务器
            成功后返回路径以及别名
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_delete_parameter(
    ["plan_id", int, 0, None],
    ["id", int, 0, None],
    ["o_id", int, 0, None]
)
def plan_worktable_snap_plugin_file_delete():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "操作成功",
        "data": {}
    }

    # 取出
    mail = flask.request.headers['Mail']
    plan_id = int(flask.request.args['plan_id'])
    pid = int(flask.request.args['id'])

    result, msg = check_plan_owner(mail, plan_id)
    if result is None or result is False:
        return msg

    # 判断有无传入uuid
    # 如果传入了uuid，则尝试删除对应的文件
    if 'uuid' in flask.request.args:
        resource_path = appconfig.get("task", "filePutDir")
        resource_path = resource_path[:-1] if resource_path[-1] == "/" else resource_path
        resource_path = "%s/%s/%s/%s" % (
            resource_path,
            plan_id,
            pid,
            flask.request.args['uuid']
        )
        if os.path.exists(resource_path) and os.path.isfile(resource_path):
            try:
                os.remove(resource_path)
            except Exception as e:
                api_logger.error("文件删除失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_file_error']
    else:
        # 暂时不作处理
        pass

    # 最后返回内容
    return response_json


def check_plan_owner(mail, plan_id):
    user_id = None
    # 取出入参
    request_head_mail = mail
    plan_id = plan_id

    # 查询测试计划基础信息，并取出所属者账户id
    try:
        mysql_plan_info = model_mysql_planinfo.query.filter(
            model_mysql_planinfo.planId == plan_id
        ).first()
    except Exception as e:
        api_logger.error("model_mysql_planinfo数据读取失败，失败原因：" + repr(e))
        return None, route.error_msgs[500]['msg_db_error']
    else:
        if mysql_plan_info is None:
            return False, route.error_msgs[201]['msg_no_plan']
        else:
            plan_user_id = mysql_plan_info.ownerId

    # 查询账户信息，并取出账户id
    try:
        mysql_userinfo = model_mysql_userinfo.query.filter(
            model_mysql_userinfo.userEmail == request_head_mail
        ).first()
        api_logger.debug("model_mysql_userinfo数据读取成功")
    except Exception as e:
        api_logger.error("model_mysql_userinfo数据读取失败，失败原因：" + repr(e))
        return None, route.error_msgs[500]['msg_db_error']
    else:
        if mysql_userinfo is None:
            return False, route.error_msgs[201]['msg_no_user']
        else:
            request_user_id = mysql_userinfo.userId

    # 如果操作者和计划拥有者不是同一人，则报错
    if plan_user_id != request_user_id:
        return False, route.error_msgs[201]['msg_plan_notopen']
    else:
        return True, None
