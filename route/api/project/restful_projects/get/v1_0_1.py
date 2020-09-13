# -*- coding: utf-8 -*-

import flask
import route

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_userinfo
from model.mysql import model_mysql_project
from model.mysql import model_mysql_projectMember


@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['admin', bool, None, None],
    ['keyword', str, 0, 50],
)
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
    request_admin = flask.request.args['admin']
    request_keyword = flask.request.args['keyword']

    print(request_admin)
    print(type(request_admin))
    # 根据是否管理
    # true返回管理的项目
    # false返回参与的项目
    if str(request_admin)=='true':

        mysql_project_list_query = mysqlpool.session.query(
            model_mysql_project,
            model_mysql_project.id.label('id'),
            model_mysql_project.name.label("title"),
            model_mysql_project.description.label("description"),
            model_mysql_project.userId.label("userId"),
            model_mysql_project.status.label("status"),
            model_mysql_userinfo.userNickName.label("nickName"),
            model_mysql_userinfo.userHeadIconUrl.label("iconUrl"),
            model_mysql_project.coverOssPath.label("coverOssPath"),
            model_mysql_project.createTime.label("createTime")
        ).join(
            model_mysql_projectMember,
            model_mysql_project.id == model_mysql_projectMember.projectId
        ).join(
            model_mysql_userinfo,
            model_mysql_projectMember.userId == model_mysql_userinfo.userId
        ).filter(
            model_mysql_project.status != -1,
            model_mysql_projectMember.status == 1,
            model_mysql_projectMember.userId == request_userid,
            model_mysql_projectMember.type == 1
        )
    else:

        mysql_project_list_query = mysqlpool.session.query(
            model_mysql_project,
            model_mysql_project.id.label('id'),
            model_mysql_project.name.label("title"),
            model_mysql_project.description.label("description"),
            model_mysql_project.userId.label("userId"),
            model_mysql_project.status.label("status"),
            model_mysql_userinfo.userNickName.label("nickName"),
            model_mysql_userinfo.userHeadIconUrl.label("iconUrl"),
            model_mysql_project.coverOssPath.label("coverOssPath"),
            model_mysql_project.createTime.label("createTime")
        ).join(
            model_mysql_projectMember,
            model_mysql_project.id == model_mysql_projectMember.projectId
        ).join(
            model_mysql_userinfo,
            model_mysql_projectMember.userId == model_mysql_userinfo.userId
        ).filter(
            model_mysql_project.status != -1,
            model_mysql_projectMember.status == 1,
            model_mysql_projectMember.userId == request_userid,
            model_mysql_projectMember.type.in_([1,2])
        )


    if request_keyword != '':
        mysql_project_list_query = mysql_project_list_query.filter(
            model_mysql_project.name.like('%' + request_keyword + '%'),
        )

    # 查询管理的项目
    try:
        mysql_project_list = mysql_project_list_query.all()
    except Exception as e:
        api_logger.error("项目数据查询失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']

    for mpl in mysql_project_list:
        single_project_data = {
            "id": mpl.id,
            "title": mpl.title,
            "description": mpl.description,
            "userId": mpl.userId,
            "nickName": mpl.nickName,
            "iconUrl": mpl.iconUrl,
            "status": mpl.status,
            "coverOssPath": mpl.coverOssPath,
            "createTime": str(mpl.createTime),
            "members": []
        }
        # 依次查询项目的参与人
        try:
            mysql_project_member_list = mysqlpool.session.query(
                model_mysql_projectMember,
                model_mysql_projectMember.id,
                model_mysql_userinfo.userId.label('userId'),
                model_mysql_userinfo.userNickName.label('nickName'),
                model_mysql_userinfo.userHeadIconUrl.label('iconUrl')
            ).join(
                model_mysql_userinfo,
                model_mysql_projectMember.userId == model_mysql_userinfo.userId
            ).filter(
                model_mysql_projectMember.projectId == mpl.id,
                model_mysql_projectMember.status == 1
            ).order_by(
                model_mysql_projectMember.id.asc()
            ).all()
        except Exception as e:
            api_logger.error("项目数据查询失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            for mpml in mysql_project_member_list:
                single_project_data['members'].append({
                    'userId': mpml.userId,
                    'nickName': mpml.nickName,
                    'iconUrl': mpml.iconUrl
                })
        response_json['data'].append(single_project_data)

    # 最后返回内容
    return response_json
