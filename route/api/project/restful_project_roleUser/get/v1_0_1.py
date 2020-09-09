# -*- coding: utf-8 -*-

import flask

import route


from handler.log import api_logger

from model.mysql import model_mysql_project
from model.mysql import model_mysql_projectMember
from model.mysql import model_mysql_userinfo
from model.mysql import model_mysql_roleinfo
"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断角色是否存在
            获取角色成员（支持keyword搜索）
            返回基础信息
"""


@route.check_user
@route.check_token
# @route.check_auth
@route.check_get_parameter(
    ['roleId', int, 1, None],
    ['nickname', str, None, None]
)
def key_projectroleUser_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data":[]
    }

    # 取出入参

    role_id = flask.request.args['roleId']

    keyword = flask.request.args['nickname']

    # 查询角色基础信息
    try:
        mysql_role_info = model_mysql_roleinfo.query.filter(
            model_mysql_roleinfo.roleId== role_id,model_mysql_roleinfo.roleStatus==1
        ).first()


    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    #判断数据是否存在
    if mysql_role_info is None:

        return route.error_msgs[201]['msg_no_role']
    else:
        # 查看角色用户

        try:
            mysql_roleUser_info = model_mysql_userinfo.query.filter(
                model_mysql_userinfo.userRoleId == role_id, model_mysql_userinfo.userStatus == 1
            ).all()


        except Exception as e:
            api_logger.error("model_mysql_depository，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        if mysql_roleUser_info is None:
            return route.error_msgs[201]['msg_no_data']
        else:
            for mpti in mysql_roleUser_info:
                # 根据关键字进行数据过滤
                if keyword != '':

                    if mpti.userNickName.find(keyword) != -1:
                        response_json['data'].append({
                            "id": mpti.userId,
                            "nickName": mpti.userNickName,
                        })

                    else:
                        pass

                else:
                    response_json['data'].append({
                        "id": mpti.userId,
                        "nickName": mpti.userNickName,

                    })


    # 最后返回内容
    return response_json
