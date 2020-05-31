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
from model.redis import model_redis_userinfo

"""
    接口测试计划下插件本身相关
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            delete-1.删除对应插件的文件夹，仅支持单个删除
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_delete_parameter(
    ["plan_id", int, 0, None],
    ["pid", int, 0, None]
)
def plan_worktable_snap_plugin_delete():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {}
    }

    # 取出
    mail = flask.request.headers['Mail']
    plan_id = int(flask.request.args['plan_id'])
    pid = int(flask.request.args['pid'])

    result, msg = check_plan_owner(mail, plan_id)
    if result is None or result is False:
        return msg

    resource_path = appconfig.get("task", "filePutDir")
    resource_path = resource_path[:-1] if resource_path[-1] == "/" else resource_path
    resource_path = "%s/%s/%s" % (
        resource_path,
        plan_id,
        pid
    )
    if os.path.exists(resource_path) and os.path.isdir(resource_path):
        try:
            shutil.rmtree(resource_path)
        except Exception as e:
            api_logger.error("文件删除失败，失败原因：" + repr(e))
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

    # 查询缓存中账户信息，并取出账户id
    redis_userinfo = model_redis_userinfo.query(user_email=request_head_mail)
    # 如果缓存中没查到，则查询mysql
    if redis_userinfo is None:
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
    else:
        # 格式化缓存基础信息内容
        try:
            redis_userinfo_json = json.loads(redis_userinfo.decode("utf8"))
            api_logger.debug("缓存账户数据json格式化成功")
        except Exception as e:
            api_logger.error("缓存账户数据json格式化失败，失败原因：" + repr(e))
            return None, route.error_msgs[500]['msg_json_format_fail']
        else:
            request_user_id = redis_userinfo_json['userId']

    # 如果操作者和计划拥有者不是同一人，则报错
    if plan_user_id != request_user_id:
        return False, route.error_msgs[201]['msg_plan_notopen']
    else:
        return True, None
