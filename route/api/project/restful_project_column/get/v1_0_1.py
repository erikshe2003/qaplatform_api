# -*- coding: utf-8 -*-

import flask
import route

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_case
from model.mysql import model_mysql_project


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['id', int, 1, None],
    ['keyword', str, 0, 200]
)
def key_projectcolumn_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据获取成功",
        "data": {}
    }

    # 取出入参
    project_id = flask.request.args['id']
    request_keyword = flask.request.args['keyword']

    # 查询项目是否存在
    try:
        mysql_project_info = model_mysql_project.query.filter(
            model_mysql_project.id == project_id,
            model_mysql_project.status != -1
        ).first()
    except Exception as e:
        api_logger.error("项目基础信息查询失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    # 判断数据是否存在
    if mysql_project_info is None:
        return route.error_msgs[201]['msg_no_project']

    # 查看仓库下面的模块
    mysql_column_info_query = mysqlpool.session.query(
        model_mysql_case.id,
        model_mysql_case.title,
        model_mysql_case.depositoryId,
        model_mysql_case.columnId,
        model_mysql_case.index,
        model_mysql_case.columnLevel,
        model_mysql_case.type,
        model_mysql_case.userId
    ).filter(
        model_mysql_case.depositoryId == mysql_project_info.depositoryId,
        model_mysql_case.type == 1,
        model_mysql_case.status == 1
    )

    if request_keyword != '':
        mysql_column_info_query = mysql_column_info_query.filter(
            model_mysql_case.title.like('%' + request_keyword + '%'),
        )

    try:
        mysql_column_info = mysql_column_info_query.order_by(
            model_mysql_case.columnLevel.asc(),
            model_mysql_case.index.asc()
        ).all()
    except Exception as e:
        api_logger.error("项目数据查询失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        # 将第一个值选中
        response_json['data'] = {
            'id': 0,
            'title': '全部目录',
            'depositoryId': mysql_project_info.depositoryId,
            'columnId': 0,
            'index': 0,
            'columnLevel': 0,
            'type': 1,
            'userId': 0,
            'expand': True,
            'selected': False,
            'contextmenu': True,
            'children': []
        }
        if len(mysql_column_info) != 0:
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
            response_json['data']['children'] = recurse_list_to_tree(0, {})

    # 最后返回内容
    return response_json
