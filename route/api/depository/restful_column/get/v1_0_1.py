# -*- coding: utf-8 -*-

import flask

import route


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
        "data": {
            "id": 0,
            "title": None,
            "type": 1,
            "children": []
        }
    }
    # 取出入参

    depository_id = flask.request.args['id']

    # 查询仓库是否存在
    try:
        mysql_depository_info = model_mysql_depository.query.filter(
            model_mysql_depository.id == depository_id
        ).first()


    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    #判断数据是否存在
    if mysql_depository_info is None:

        return route.error_msgs[201]['msg_no_depository']

    #查看仓库下面的模块

    try:
        mysql_column_info = model_mysql_case.query.filter(
            model_mysql_case.depositoryId == depository_id,
            model_mysql_case.type==1,
            model_mysql_case.columnId==0,
            model_mysql_case.status == 1
        ).first()


    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    if mysql_column_info is None:
        return route.error_msgs[201]['msg_no_catalogue']
    else:
        response_json['data']['id']=mysql_column_info.id
        response_json['data']['title']=mysql_column_info.title
        response_json['data']['children'].extend(search_child_column(mysql_column_info.id))


    # 最后返回内容
    return response_json


def search_child_column(columnId):
    count=0
    child_column=[]
    try:
        mysql_child_info = model_mysql_case.query.filter(
            model_mysql_case.columnId == columnId,model_mysql_case.type==1,model_mysql_case.status==1

        ).all()
        api_logger.debug("账户基础信息读取成功")
    except Exception as e:
        api_logger.error("账户基础信息读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_child_info is None:
            return None
        else:
            for mqti in mysql_child_info:
                child_column.append({
                    "id":mqti.id,
                    "title":mqti.title,
                    "type": 1,
                    "children": []
                })

                child_column[count]['children'].extend(search_child_column(mqti.id))
                count+=1
    return child_column