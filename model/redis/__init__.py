# -*- coding: utf-8 -*-

from .rolePermission_r import RolePermissionR
from .userToken_r import UserTokenR
from .apiAuth_r import ApiAuthR
from .apiTestPlanWorkTable_r import ApiTestPlanWorkTableR

from handler.log import sys_logger

logmsg = "系统初始化|准备初始化redis数据库模型"
sys_logger.info(logmsg)
try:
    # 实例化redis的model
    modle_redis_apitestplanworktable = ApiTestPlanWorkTableR()
    model_redis_rolepermission = RolePermissionR()
    model_redis_usertoken = UserTokenR()
    model_redis_apiauth = ApiAuthR()
    logmsg = "系统初始化|redis数据库模型初始化成功"
    sys_logger.debug(logmsg)
except Exception as e:
    logmsg = "系统初始化|redis数据库模型初始化失败，失败原因：" + repr(e)
    sys_logger.error(logmsg)
    raise RuntimeError(logmsg)
