# -*- coding: utf-8 -*-

import flask
import route
import datetime

from handler.pool import mysqlpool
from handler.log import api_logger

from model.mysql import model_mysql_case

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作

            判断目录是否存在
            最后返回新增结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_delete_parameter(
    ['id', int, 1, None],
    ['depositoryId', int, 1, None],
)
def key_column_delete():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "数据删除成功",
        "data": None
    }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    column_id = flask.request.args['id']
    depository_id = flask.request.args['depositoryId']

    # 判断目录是否存在
    try:
        mysql_column_info = model_mysql_case.query.filter(
            model_mysql_case.id == column_id,
            model_mysql_case.depositoryId == depository_id,
            model_mysql_case.type == 1
        ).first()
        api_logger.debug("仓库目录信息读取成功")
    except Exception as e:
        api_logger.error("仓库目录信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        mysql_column_info.status = -1
        mysql_column_info.updateUser = request_user_id
        mysql_column_info.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if mysql_column_info is None:
            return route.error_msgs[201]['msg_no_catalogue']
        else:
            # 删除目录下所有case/column
            try:
                mysql_children_info = model_mysql_case.query.filter(
                    model_mysql_case.columnId == column_id
                ).all()
                api_logger.debug("仓库目录信息读取成功")
            except Exception as e:
                api_logger.error("仓库目录信息读取失败，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            else:
                if len(mysql_children_info) != 0:
                    for mci in mysql_children_info:
                        mci.status = -1
                        mci.updateUser = request_user_id
                        mci.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        try:
            mysqlpool.session.commit()
            api_logger.error("仓库目录信息更新成功")
        except Exception as e:
            api_logger.error("仓库目录信息更新失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']

    # 最后返回内容
    return response_json
