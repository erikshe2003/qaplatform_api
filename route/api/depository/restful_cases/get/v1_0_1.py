# -*- coding: utf-8 -*-

import flask
import route

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
            判断用例是否存在
            返回操作结果
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['depositoryId', int, 1, None],
    ['columnId', int, 0, None],
    ['keyWord', str, None, None]
)
def key_cases_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据获取成功",
        "data": []
    }

    # 取出必传入参
    depository_id = flask.request.args['depositoryId']
    column_id = flask.request.args['columnId']
    key_word = flask.request.args['keyWord']

    # 判断仓库是否存在
    try:
        mysql_depository_info = model_mysql_depository.query.filter(
            model_mysql_depository.id == depository_id
        ).first()
        api_logger.error("仓库数据读取成功")
    except Exception as e:
        api_logger.error("仓库数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_depository_info is None:
            return route.error_msgs[201]['msg_no_depository']

    # 判断目录是否存在
    try:
        mysql_column_info = model_mysql_case.query.filter(
            model_mysql_case.id == column_id,
            model_mysql_case.status == 1,
            model_mysql_case.type == 1,
            model_mysql_case.depositoryId == depository_id
        ).first()
        api_logger.error("仓库目录数据读取成功")
    except Exception as e:
        api_logger.error("仓库目录数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_column_info is None:
            return route.error_msgs[201]['msg_no_catalogue']

    # 查询目录下的用例清单
    # 1．查看仓库最新归档用例的数据筛选条件为depositoryId取实际id&status=1&veri=3&arch=2
    mysql_cases_info_query = mysqlpool.session.query(
        model_mysql_case.id,
        model_mysql_case.title,
        model_mysql_case.depositoryId,
        model_mysql_case.projectId,
        model_mysql_case.columnId,
        model_mysql_case.index,
        model_mysql_case.level,
        model_mysql_case.status,
        model_mysql_case.veri,
        model_mysql_case.arch
    ).filter(
        model_mysql_case.depositoryId == depository_id,
        model_mysql_case.columnId == column_id,
        model_mysql_case.type == 2,
        model_mysql_case.status == 1,
        model_mysql_case.veri == 3,
        model_mysql_case.arch == 2,
    )
    if key_word != '':
        mysql_cases_info_query = mysql_cases_info_query.filter(
            model_mysql_case.title.like('%'+key_word+'%'),
        )
    try:
        mysql_cases_info = mysql_cases_info_query.all()
        api_logger.error("仓库目录数据读取成功")
    except Exception as e:
        api_logger.error("仓库目录数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        for mci in mysql_cases_info:
            response_json['data'].append({
                'id': mci.id,
                'title': mci.title,
                'depositoryId': mci.depositoryId,
                'projectId': mci.projectId,
                'columnId': mci.columnId,
                'index': mci.index,
                'level': mci.level,
                'status': mci.status,
                'veri': mci.veri,
                'arch': mci.arch
            })

    return response_json
