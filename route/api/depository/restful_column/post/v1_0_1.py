# -*- coding: utf-8 -*-

import flask
import route
import datetime

from handler.pool import mysqlpool
from handler.log import api_logger

from sqlalchemy.sql import func

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
            然后判断目录是否存在
            最后返回新增结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['title', str, 1, 200],
    ['columnId', int, 0, None],
    ['depositoryId', int, 1, None],
)
def key_column_post():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "数据新增成功",
        "data": None
    }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    column_title = flask.request.json['title']
    column_id = flask.request.json['columnId']
    depository_id = flask.request.json['depositoryId']

    # 判断仓库是否存在
    try:
        mysql_depository = model_mysql_depository.query.filter(
            model_mysql_depository.id == depository_id
        ).first()
        api_logger.error("仓库数据读取成功")
    except Exception as e:
        api_logger.error("仓库数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_depository is None:
            return route.error_msgs[201]['msg_no_depository']

    # 新增目录
    # 获取父级目录下子目录最大index
    try:
        mysql_children_column_max_index = mysqlpool.session.query(
            func.max(model_mysql_case.index)
        ).filter(
            model_mysql_case.columnId == column_id,
            model_mysql_case.depositoryId == depository_id,
            model_mysql_case.status != -1,
            model_mysql_case.type == 1
        ).first()[0]
        api_logger.debug("仓库目录信息读取成功")
    except Exception as e:
        api_logger.error("仓库目录信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    new_column_info = model_mysql_case(
        title=column_title,
        depositoryId=depository_id,
        columnId=column_id,
        index=mysql_children_column_max_index + 1 if mysql_children_column_max_index is not None else 1,
        level=0,
        type=1,
        status=1,
        userId=request_user_id,
        createTime=str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    # 判断是否存在父级目录
    if column_id == 0:
        #
        new_column_info.columnLevel = 1
    else:
        try:
            mysql_column_info = model_mysql_case.query.filter(
                model_mysql_case.id == column_id,
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
        #
        new_column_info.columnLevel = mysql_column_info.columnLevel + 1

    try:
        mysqlpool.session.add(new_column_info)
        mysqlpool.session.commit()
        api_logger.error("仓库目录信息新增成功")
    except Exception as e:
        api_logger.error("仓库目录信息新增失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        response_json['data'] = {
            'id': new_column_info.id,
            'title': new_column_info.title,
            'depositoryId': new_column_info.depositoryId,
            'columnId': new_column_info.columnId,
            'index': new_column_info.index,
            'columnLevel': new_column_info.columnLevel,
            'type': new_column_info.type,
            'level': new_column_info.level,
            'userId': new_column_info.userId,
            'expand': True,
            'selected': False,
            'contextmenu': True,
        }

    # 最后返回内容
    return response_json
