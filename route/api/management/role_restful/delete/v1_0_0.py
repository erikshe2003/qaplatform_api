# -*- coding: utf-8 -*-

import flask
import route

from handler.log import api_logger
from handler.pool import mysqlpool

from model.mysql import model_mysql_roleinfo
from model.mysql import model_mysql_rolepermission
from model.redis import model_redis_rolepermission
from model.redis import model_redis_apiauth


# 删除角色-api路由
# ----校验
# 1.校验传参
# 2.校验账户是否存在
# 3.校验账户操作令牌
# 4.校验账户所属角色是否有此api的访问权限
# ----操作
# 4.检查角色是否存在
# 5.检查角色是否可删除
# 6.根据id删除角色
@route.check_user
@route.check_token
@route.check_auth
@route.check_get_parameter(
    ['role_id', int, 1, None]
)
def role_delete():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "",
        "data": {}
    }

    # 取出传入参数值
    requestvalue_roleid = int(flask.request.args["role_id"])

    # 5.尝试按照id删除角色以及角色的权限信息
    # 先删除mysql中roleInfo的信息
    try:
        ri_mysql = model_mysql_roleinfo.query.filter_by(roleId=requestvalue_roleid).all()
        logmsg = "数据库中账号信息读取成功"
        api_logger.error(logmsg)
    except Exception as e:
        logmsg = "数据库中账号信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 删
        [mysqlpool.session.delete(rim) for rim in ri_mysql]
        mysqlpool.session.commit()
    # 然后删除mysql中rolePermission的信息
    try:
        rp_mysql = model_mysql_rolepermission.query.filter_by(roleId=requestvalue_roleid).all()
        logmsg = "数据库中角色权限信息读取成功"
        api_logger.error(logmsg)
    except Exception as e:
        logmsg = "数据库中角色权限信息读取失败，失败原因：" + repr(e)
        api_logger.error(logmsg)
    else:
        # 删
        [mysqlpool.session.delete(rpm) for rpm in rp_mysql]
        mysqlpool.session.commit()
    # 删除redis中rolePermission的信息
    deleteflag = model_redis_rolepermission.delete(role_id=requestvalue_roleid)
    if deleteflag is True:
        logmsg = "缓存中角色权限信息删除成功"
        api_logger.debug(logmsg)
    else:
        logmsg = "缓存中角色权限信息删除失败"
        api_logger.error(logmsg)
    # 删除redis中apiAuth的信息
    deleteflag = model_redis_apiauth.delete(role_id=requestvalue_roleid)
    if deleteflag is True:
        logmsg = "缓存中角色权限信息删除成功"
        api_logger.debug(logmsg)
    else:
        logmsg = "缓存中角色权限信息删除失败"
        api_logger.error(logmsg)

    # 8.返回成功信息
    response_json["error_msg"] = "操作成功"
    # 最后返回内容
    return response_json

