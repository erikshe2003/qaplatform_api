# -*- coding: utf-8 -*-

import route

from handler.log import api_logger

from model.mysql import model_mysql_depository

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            权限人员才可见
            返回仓库列表
"""


@route.check_user
@route.check_token
@route.check_auth
def key_depositories_get():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "数据获取成功",
        "data": []
    }

    # 查询项目信息基础信息
    try:
        mysql_depositories_info = model_mysql_depository.query.filter().all()
    except Exception as e:
        api_logger.error("表model_mysql_subject读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        for mpti in mysql_depositories_info:
            response_json["data"].append({
                "id": mpti.id,
                "name": mpti.name,
                "description": mpti.description,
                "userId": mpti.userId,
                "baseProjectId": mpti.baseProjectId,
                "createTime": str(mpti.createTime)
            })

    # 最后返回内容
    return response_json
