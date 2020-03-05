# -*- coding: utf-8 -*-

import os
import flask
import json
import mimetypes
import uuid
import route

from handler.log import api_logger
from handler.config import appconfig

from route.api.plan import api_plan

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_userinfo
from model.redis import model_redis_userinfo

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


@api_plan.route('/parameterizeFile', methods=["post", "delete", "get"])
@route.check_user
@route.check_token
@route.check_auth
@route.check_form_parameter({
    "files": [
        ["file", object, 0, 50*1024*1024]
    ],
    "forms": [
        ["plan_id", int, 0, None],
        ["id", int, 0, None],
        ["o_id", int, 0, None]
    ]
})
@route.check_delete_parameter(
    ["plan_id", int, 0, None],
    ["id", int, 0, None],
    ["o_id", int, 0, None]
)
@route.check_get_parameter(
    ["plan_id", int, 0, None],
    ["id", int, 0, None],
    ["o_id", int, 0, None],
    ["uuid", str, 0, None]
)
def parameterize_file():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {}
    }

    # POST - 上传文件
    # DELETE - 删除插件拥有的文件
    # 如果传了文件uuid名称，则删除对应的；如果没传，则删除所有
    if flask.request.method == "POST":
        # 初始化返回内容
        response_json['data'] = {
            "name": "",
            "uuid": ""
        }

        result, msg = check_plan_owner(flask.request.headers['Mail'], flask.request.form['plan_id'])
        if result is None or result is False:
            return msg

        # 得到uuid转换后的文件名
        request_file = flask.request.files['file']
        response_json['data']['name'] = request_file.filename
        response_json['data']['uuid'] = "%s.%s" % (uuid.uuid1().hex, request_file.filename.split('.')[-1])

        # 将文件存储至指定路径下
        # 按照：指定路径/plan_id/id下
        resource_path = appconfig.get("task", "filePutDir")
        resource_path = resource_path[:-1] if resource_path[-1] == "/" else resource_path
        resource_path = "%s/%s/%s" % (resource_path, flask.request.form['plan_id'], flask.request.form['id'])

        # 根据配置文件中的路径，判断账户私有文件夹是否存在
        if os.path.exists(resource_path) is False or os.path.isdir(resource_path) is False:
            # 新建文件夹
            try:
                os.makedirs(resource_path)
            except Exception as e:
                api_logger.error("文件夹创建失败，失败原因：" + repr(e))
                return route.error_msgs['msg_file_error']
        # 将文件保存至指定路径
        try:
            request_file.save("%s/%s" % (resource_path, response_json['data']['uuid']))
        except Exception as e:
            api_logger.error("文件保存失败，失败原因：" + repr(e))
            return route.error_msgs['msg_file_error']
    elif flask.request.method == "DELETE":
        result, msg = check_plan_owner(flask.request.headers['Mail'], flask.request.form['plan_id'])
        if result is None or result is False:
            return msg

        # 判断有无传入uuid
        # 如果传入了uuid，则尝试删除对应的文件
        if 'uuid' in flask.request.form:
            resource_path = appconfig.get("task", "filePutDir")
            resource_path = resource_path[:-1] if resource_path[-1] == "/" else resource_path
            resource_path = "%s/%s/%s/%s" % (
                resource_path,
                flask.request.form['plan_id'],
                flask.request.form['id'],
                flask.request.form['uuid']
            )
            if os.path.exists(resource_path) and os.path.isfile(resource_path):
                try:
                    os.remove(resource_path)
                except Exception as e:
                    api_logger.error("文件删除失败，失败原因：" + repr(e))
                    return route.error_msgs['msg_file_error']
        else:
            # 暂时不作处理
            pass
    elif flask.request.method == "GET":
        result, msg = check_plan_owner(flask.request.headers['Mail'], flask.request.args['plan_id'])
        if result is None or result is False:
            return msg

        resource_path = appconfig.get("task", "filePutDir")
        resource_path = resource_path[:-1] if resource_path[-1] == "/" else resource_path
        resource_path = "%s/%s/%s/%s" % (
            resource_path,
            flask.request.args['plan_id'],
            flask.request.args['id'],
            flask.request.args['uuid']
        )
        if os.path.exists(resource_path) and os.path.isfile(resource_path):
            # memory_file = io.BytesIO()
            # zf = zipfile.ZipFile(memory_file, "a", zipfile.ZIP_DEFLATED)
            # zf.write(resource_path, flask.request.args['uuid'])
            # zf.close()
            # memory_file.seek(0, 0)
            #     mimetypes.guess_type(resource_path)[0],
            #     chardet.detect(memory_file.read())['encoding'].replace('-', '').lower()
            return flask.send_file(
                resource_path,
                mimetype=mimetypes.guess_type(resource_path)[0],
                attachment_filename='%s.zip' % flask.request.args['uuid'],
                as_attachment=True
            )

    # 最后返回内容
    return json.dumps(response_json)


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
        return None, route.error_msgs['msg_db_error']
    else:
        if mysql_plan_info is None:
            return False, route.error_msgs['msg_no_plan']
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
            return None, route.error_msgs['msg_db_error']
        else:
            if mysql_userinfo is None:
                return False, route.error_msgs['msg_no_user']
            else:
                request_user_id = mysql_userinfo.userId
    else:
        # 格式化缓存基础信息内容
        try:
            redis_userinfo_json = json.loads(redis_userinfo.decode("utf8"))
            api_logger.debug("缓存账户数据json格式化成功")
        except Exception as e:
            api_logger.error("缓存账户数据json格式化失败，失败原因：" + repr(e))
            return None, route.error_msgs['msg_json_format_fail']
        else:
            request_user_id = redis_userinfo_json['userId']

    # 如果操作者和计划拥有者不是同一人，则报错
    if plan_user_id != request_user_id:
        return False, route.error_msgs['msg_plan_notopen']
    else:
        return True, None
