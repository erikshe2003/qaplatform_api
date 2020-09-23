# -*- coding: utf-8 -*-

import flask
import route

from sqlalchemy import or_, and_

from handler.log import api_logger

from model.mysql import model_mysql_case


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['projectId', int, 1, None],
    ['columnId', int, 1, None],
    ['keyWord', str, None, None],
    ['thisProject', int, 0, 1]
)
def key_cases_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "数据获取成功",
        "data": []
    }

    # 取出必传入参
    project_id = int(flask.request.args['projectId'])
    column_id = int(flask.request.args['columnId'])
    key_word = flask.request.args['keyWord']
    only_project_self = int(flask.request.args['thisProject'])

    # 判断目录是否存在，并获取仓库id
    try:
        mysql_column_info = model_mysql_case.query.filter(
            model_mysql_case.id == column_id,
            model_mysql_case.status != -1,
            model_mysql_case.type == 1
        ).first()
    except Exception as e:
        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_column_info is None:
            return route.error_msgs[201]['msg_no_column']

    # 根据仓库id项目id目录id查询项目内的用例清单
    # 获取项目中带originalCaseId的数据
    original_case_id_list = [0]
    try:
        mysql_original_case_info = model_mysql_case.query.filter(
            model_mysql_case.columnId == column_id,
            model_mysql_case.projectId == project_id,
            model_mysql_case.status != -1,
            model_mysql_case.type == 2,
            model_mysql_case.originalCaseId != 0
        ).all()
    except Exception as e:
        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        for mqti in mysql_original_case_info:
            original_case_id_list.append(mqti.originalCaseId)

    # 查询时排除original_case_id_list
    mysql_cases_info_query = model_mysql_case.query.filter(
        or_(
            and_(
                # 仓库下状态正常、已归档且未被本项目引用的用例
                model_mysql_case.columnId == column_id,
                model_mysql_case.depositoryId == mysql_column_info.depositoryId,
                model_mysql_case.status != -1,
                model_mysql_case.type == 2,
                model_mysql_case.arch == 2,
                model_mysql_case.veri == 3,
                model_mysql_case.id.notin_(original_case_id_list)
            ),
            and_(
                model_mysql_case.columnId == column_id,
                model_mysql_case.projectId == project_id,
                model_mysql_case.status.in_([1, 3]),
                model_mysql_case.type == 2
            )
        )
    )
    if key_word != '':
        mysql_cases_info_query = mysql_cases_info_query.filter(
            model_mysql_case.title.like('%'+key_word+'%'),
        )
    try:
        mysql_cases_info = mysql_cases_info_query.order_by(
            model_mysql_case.index
        ).all()
    except Exception as e:
        api_logger.error("用例读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        for mci in mysql_cases_info:
            response_json['data'].append({
                'id': mci.id,
                'columnId': mci.columnId,
                'projectId': mci.projectId,
                'depositoryId': mci.depositoryId,
                'title': mci.title,
                'level': mci.level,
                'index': mci.index,
                'veri': mci.veri,
                'status': mci.status,
                'arch': mci.arch
            })

    return response_json
