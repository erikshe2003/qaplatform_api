# -*- coding: utf-8 -*-

import flask

import route


from handler.log import api_logger

from model.mysql import model_mysql_project
from model.mysql import model_mysql_projectMember

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            根据用户查询符合条件的仓库信息
            返回测试仓库基础信息包括成员信息
"""


@route.check_user
@route.check_token
@route.check_auth

def key_projects_get():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据获取成功",
    "data": []
    }

    # 取出入参
    count = 0

    request_userid = flask.request.headers['userId']


    #查询符合条件的项目id
    try:
        mysql_projectMember_info = model_mysql_projectMember.query.filter(
            model_mysql_projectMember.userId ==request_userid,model_mysql_projectMember.status==1
        ).all()

    except Exception as e:
        api_logger.error("model_mysql_depository，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    if mysql_projectMember_info is None:
        return route.error_msgs[201]['msg_no_project']
    else:

        for mqit in mysql_projectMember_info:

            # 查询项目基础信息
            try:
                mysql_project_info = model_mysql_project.query.filter(
                    model_mysql_project.id == mqit.projectId,model_mysql_project.status!=-1
                ).first()


            except Exception as e:
                api_logger.error("model_mysql_depository，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']

            # 判断数据是否存在
            if mysql_project_info is None:

                continue
            else:
                response_json["data"].append({
                    "id": mysql_project_info.id,
                    "name": mysql_project_info.name,
                    "description": mysql_project_info.description,
                    "userId": mysql_project_info.userId,
                    "coverOssPath": mysql_project_info.coverOssPath,
                    "createTime": str(mysql_project_info.createTime),
                    "members":[]
                })
            #查看项目成员

            try:
                mysql_projectMembers_info = model_mysql_projectMember.query.filter(
                    model_mysql_projectMember.projectId == mqit.projectId,model_mysql_projectMember.status==1
                ).all()


            except Exception as e:
                api_logger.error("model_mysql_depository，失败原因：" + repr(e))
                return route.error_msgs[500]['msg_db_error']
            if mysql_projectMembers_info is None:
                pass
            else:
                for mptis in mysql_projectMembers_info:
                    response_json['data'][count]['members'].append({
                        "id": mptis.id,
                        "userId": mptis.userId,
                        "type": str(mptis.type),
                        "createTime": str(mptis.createTime)
                    })
            count+=1

    # 最后返回内容
    return response_json
