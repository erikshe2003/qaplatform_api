# -*- coding: utf-8 -*-

import os
import shutil
import flask
import json
import route

from handler.log import api_logger
from handler.config import appconfig

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_userinfo

"""
    接口测试计划复制插件接口，仅支持一对一复制
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            将a插件的文件夹整体复制一份新的给b插件
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ["plan_id", int, 0, None],
    ["a_id", int, 0, None],
    ["b_id", int, 0, None]
)
def plan_worktable_snap_plugin_post():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "操作成功",
        "data": {}
    }

    # 如果传了文件uuid名称，则删除对应的；如果没传，则删除所有
    result, msg = check_plan_owner(flask.request.headers['Mail'], flask.request.json['plan_id'])
    if result is None or result is False:
        return msg

    # 尝试将a文件夹拷贝成b文件夹
    # 按照：指定路径/plan_id/id下
    resource_path = appconfig.get("task", "filePutDir")
    resource_path = resource_path[:-1] if resource_path[-1] == "/" else resource_path
    resource_path_a = "%s/%s/%s" % (
        resource_path,
        flask.request.json['plan_id'],
        flask.request.json['a_id']
    )
    resource_path_b = "%s/%s/%s" % (
        resource_path,
        flask.request.json['plan_id'],
        flask.request.json['b_id']
    )
    # 如果b文件夹存在，则删除
    if os.path.exists(resource_path_b) and os.path.isdir(resource_path_b):
        # 删除文件夹
        try:
            shutil.rmtree(resource_path_b)
        except Exception as e:
            api_logger.error("文件夹删除失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_file_error']
    if os.path.exists(resource_path_a) and os.path.isdir(resource_path_a):
        # 新建文件夹
        try:
            shutil.copytree(resource_path_a, resource_path_b)
        except Exception as e:
            api_logger.error("文件夹复制失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_file_error']

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
