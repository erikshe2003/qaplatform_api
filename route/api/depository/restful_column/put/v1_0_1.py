# -*- coding: utf-8 -*-

import flask
import route
import datetime

from handler.pool import mysqlpool
from handler.log import api_logger

from model.mysql import model_mysql_case
from model.mysql import model_mysql_depository


"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            先判断仓库是否有效
            再判断关联目录是否有效
            然后判断目录是否存在且非顶级目录
            最后返回结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['id', int, 1, None],
    ['name', str, 1, 200],
    ['columnId', int, 0, None],
    ['depositoryId', int, 1, None],
    ['index', int, 0, None],
    ['columnLevel', int, 0, None]
)
def key_column_put():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据修改成功",
        "data": {}
   }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    column_id = flask.request.json['id']
    column_name = flask.request.json['name']
    old_related_column_id = 0
    new_related_column_id = flask.request.json['columnId']
    depository_id = flask.request.json['depositoryId']
    column_index = flask.request.json['index']
    column_level = flask.request.json['columnLevel']

    # 判断仓库是否存在
    try:
        mysql_depository = model_mysql_depository.query.filter(
            model_mysql_depository.id == depository_id
        ).first()
    except Exception as e:
        api_logger.error("仓库数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_depository is None:
            return route.error_msgs[201]['msg_no_depository']

    # 判断是否存在父级目录
    if new_related_column_id == 0:
        pass
    else:
        try:
            mysql_column_info = model_mysql_case.query.filter(
                model_mysql_case.id == new_related_column_id,
                model_mysql_case.depositoryId == depository_id,
                model_mysql_case.status == 1,
                model_mysql_case.type == 1
            ).first()
            api_logger.debug("仓库目录信息读取成功")
        except Exception as e:
            api_logger.error("仓库目录信息读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_column_info is None:
                return route.error_msgs[201]['msg_no_catalogue']

    # 判断目录是否存在
    try:
        mysql_column_info = model_mysql_case.query.filter(
            model_mysql_case.depositoryId == depository_id,
            model_mysql_case.id == column_id,
            model_mysql_case.type == 1
        ).first()
        api_logger.debug("待处理仓库目录信息读取成功")
    except Exception as e:
        api_logger.error("待处理仓库目录信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_column_info is None:
            return route.error_msgs[201]['msg_no_catalogue']
        else:
            old_related_column_id = mysql_column_info.columnId

    # 修改待修改内容旧所属同一个columnLevel下节点list的后续所有内容的index
    try:
        mysql_old_cases_info = model_mysql_case.query.filter(
            model_mysql_case.depositoryId == depository_id,
            model_mysql_case.columnId == old_related_column_id,
            model_mysql_case.status != -1,
            model_mysql_case.type == 1,
            model_mysql_case.index > mysql_column_info.index
        ).all()
        api_logger.debug("仓库旧目录信息读取成功")
    except Exception as e:
        api_logger.error("仓库旧目录信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        for moci in mysql_old_cases_info:
            moci.index -= 1
            moci.updateUserId = request_user_id
            moci.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 修改待修改内容新所属同一个columnLevel下节点list的后续所有内容的index
    try:
        mysql_new_cases_info = model_mysql_case.query.filter(
            model_mysql_case.depositoryId == depository_id,
            model_mysql_case.columnId == new_related_column_id,
            model_mysql_case.status != -1,
            model_mysql_case.type == 1,
            model_mysql_case.index >= column_index
        ).all()
        api_logger.debug("仓库新目录信息读取成功")
    except Exception as e:
        api_logger.error("仓库新目录信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        for mnci in mysql_new_cases_info:
            mnci.index += 1
            mnci.updateUserId = request_user_id
            mnci.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    mysql_column_info.status = 1
    mysql_column_info.columnId = new_related_column_id
    mysql_column_info.title = column_name
    mysql_column_info.updateUserId = request_user_id
    mysql_column_info.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    mysql_column_info.index = column_index
    mysql_column_info.columnLevel = column_level
    try:
        # 内容一起提交
        mysqlpool.session.commit()
        api_logger.debug("数据更新成功")
    except Exception as e:
        api_logger.debug("数据更新失败，失败原因:" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    # 最后返回内容
    return response_json
