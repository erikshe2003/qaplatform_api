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
            判断项目是否存在
            获取项目成员（支持keyword搜索）
            返回基础信息
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['id', int, 1, None],
    ['nickname', str, None, None]
)
def key_projectmember_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data":[]
    }
    count=0

    # 取出入参

    project_id = flask.request.args['id']

    keyword = flask.request.args['nickname']

    # 查询项目基础信息
    try:
        mysql_project_info = model_mysql_project.query.filter(
            model_mysql_project.id == project_id,model_mysql_project.status==1
        ).first()


    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    #判断数据是否存在
    if mysql_project_info is None:

        return route.error_msgs[201]['msg_no_project']
    else:
        # 查看项目成员

        try:
            mysql_projectMember_info = model_mysql_projectMember.query.filter(
                model_mysql_projectMember.projectId == project_id, model_mysql_projectMember.status == 1
            ).all()


        except Exception as e:
            api_logger.error("model_mysql_depository，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        if mysql_projectMember_info is None:
            pass
        else:
            for mpti in mysql_projectMember_info:


                #获取项目成员昵称
                try:

                    mysql_user_info = model_mysql_userinfo.query.filter(
                        model_mysql_userinfo.userId == mpti.userId
                    ).first()

                except Exception as e:
                    api_logger.error("model_mysql_depository，失败原因：" + repr(e))
                    return route.error_msgs[500]['msg_db_error']
                if mysql_user_info is None:
                    pass
                else:

                    try:

                        mysql_role_info = model_mysql_roleinfo.query.filter(
                            model_mysql_roleinfo.roleId == mysql_user_info.userRoleId,
                            model_mysql_roleinfo.roleStatus == 1
                        ).all()

                    except Exception as e:
                        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
                        return route.error_msgs[500]['msg_db_error']
                    else:
                        for xx in mysql_role_info:
                            roles = xx.roleName + ','

                    #根据关键字进行数据过滤
                    if keyword!='':
                        # 获取项目成员角色名称



                        if mysql_user_info.userNickName.find(keyword)!= -1:
                            response_json['data'].append({
                                "id": mpti.id,
                                "userId": mpti.userId,
                                "type": str(mpti.type),
                                "createTime": str(mpti.createTime),
                                "nickName": None,
                                "roles": roles
                            })
                            response_json['data'][count]['nickName'] = mysql_user_info.userNickName
                            count += 1

                    else:

                        response_json['data'].append({
                            "id": mpti.id,
                            "userId": mpti.userId,
                            "type": str(mpti.type),
                            "createTime": str(mpti.createTime),
                            "nickName": None,
                            "roles": roles
                        })
                        response_json['data'][count]['nickName'] = mysql_user_info.userNickName
                        count += 1


    # 最后返回内容
    return response_json
