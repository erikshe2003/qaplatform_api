# -*- coding: utf-8 -*-

import flask

import route


from handler.log import api_logger
from handler.pool import mysqlpool

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
            判断测试仓库是否存在
            返回测试仓库基础信息
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['id', int, 1, None]
)
def key_column_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据获取成功",
        "data": {}
    }
    # 取出入参

    depository_id = int(flask.request.args['id'])

    # 查询仓库是否存在
    try:
        mysql_depository_info = model_mysql_depository.query.filter(
            model_mysql_depository.id == depository_id
        ).first()
    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    # 判断数据是否存在
    if mysql_depository_info is None:
        return route.error_msgs[201]['msg_no_depository']

    # 查看仓库下面的模块
    try:
        mysql_column_info = mysqlpool.session.query(
            model_mysql_case.id,
            model_mysql_case.title,
            model_mysql_case.depositoryId,
            model_mysql_case.columnId,
            model_mysql_case.index,
            model_mysql_case.columnLevel,
            model_mysql_case.type,
            model_mysql_case.userId
        ).filter(
            model_mysql_case.depositoryId == depository_id,
            model_mysql_case.type == 1,
            model_mysql_case.status == 1
        ).order_by(
            model_mysql_case.columnLevel.asc(),
            model_mysql_case.index.asc()
        ).all()
    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if len(mysql_column_info) == 0:
            return response_json
        else:
            # 修改返回数据的结构
            column_info = []
            for mci in mysql_column_info:
                column_info.append({
                    'id': mci.id,
                    'title': mci.title,
                    'depositoryId': mci.depositoryId,
                    'columnId': mci.columnId,
                    'index': mci.index,
                    'columnLevel': mci.columnLevel,
                    'type': mci.type,
                    'userId': mci.userId,
                    'expand': True,
                    'selected': False,
                    'contextmenu': True,
                    'children': []
                })

            def recurse_list_to_tree(father_id, tree_node):
                tree = []
                tree_node_list = [x for x in column_info if x['columnId'] == father_id]
                if father_id == 0:
                    tree = tree_node_list
                else:
                    tree_node['children'] = tree_node_list
                if len(tree_node_list) > 0:
                    for tnl in tree_node_list:
                        recurse_list_to_tree(tnl['id'], tnl)
                return tree

            # 将第一个值选中
            response_json['data'] = {
                'id': 0,
                'title': '全部目录',
                'depositoryId': depository_id,
                'columnId': 0,
                'index': 0,
                'columnLevel': 0,
                'type': 1,
                'userId': 0,
                'expand': True,
                'selected': False,
                'contextmenu': True,
                'children': recurse_list_to_tree(0, {})
            }

    # 最后返回内容
    return response_json
