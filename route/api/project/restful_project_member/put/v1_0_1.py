# -*- coding: utf-8 -*-

import flask

import route

from handler.pool import mysqlpool

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
            判断测试项目是否存在
            添加项目成员
"""


@route.check_user
@route.check_token
@route.check_auth
@route.check_post_parameter(
    ['id', int, 1, None],
    ['userIds', str, 1, 50]

)

def key_projectmember_put():
    # 初始化返回内容
    response_json = {
    "code": 200,
    "msg": "数据修改成功",
    "data": None
   }

    # 取出必传入参
    request_user_id = flask.request.headers['UserId']
    project_id = flask.request.json['id']
    projectmembers_id = flask.request.json['userIds']


     #查询项目名称是否存在
    try:
        mysql_project = model_mysql_project.query.filter(
            model_mysql_project.id==project_id,model_mysql_project.status==1,model_mysql_project.userId==request_user_id
        ).first()
    except Exception as e:
        api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_project is None:

            return route.error_msgs[201]['msg_no_project']

    # print(request_user_id)
    # print(project_id)
    print(projectmembers_id)
    member=projectmembers_id.split(',')
    for x in member:
        print(x)
        # 查询用户是否已经存在名称是否存在
        try:
            mysql_projectMember_info= model_mysql_projectMember.query.filter(
                model_mysql_projectMember.id == project_id, model_mysql_projectMember.userId == int(x)
            ).first()
            print(mysql_projectMember_info)
        except Exception as e:
            api_logger.error("测试计划类型读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_projectMember_info is None:
                new_projectMember_info = model_mysql_projectMember(

                    projectId=project_id,
                    userId=int(x),
                    type=1,
                    status=1

                )
                mysqlpool.session.add(new_projectMember_info)
                mysqlpool.session.commit()
            else:
                print('xx')
                mysql_projectMember_info.status=1
                mysqlpool.session.commit()







        # else:
        #     mysql_project.name=project_name
        #     mysql_project.description=project_description
        #     mysql_project.coverOssPath=project_coverOssPath
        #     mysqlpool.session.commit()



    # 最后返回内容
    return response_json