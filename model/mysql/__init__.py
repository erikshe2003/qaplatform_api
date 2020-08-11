# -*- coding: utf-8 -*-

from .userUi.userInfo import UserInfo
from .userUi.rolePermission import RolePermission
from .userUi.roleInfo import RoleInfo
from .userUi.operationInfo import OperationInfo
from .userUi.userOperationRecord import UserOperationRecord
from .userUi.functionInfo import FunctionInfo
from .userUi.functionOrg import FunctionOrg
from .userUi.apiInfo import ApiInfo
from .userUi.planInfo import PlanInfo
from .userUi.planType import PlanType
from .userUi.taskInfo import TaskInfo
from .userUi.taskAssign import TaskAssign
from .userUi.workerInfo import WorkerInfo
from .userUi.tableSnap import TableSnap
from .userUi.subject import subject
from handler.log import sys_logger


logmsg = "系统初始化|准备初始化mysql数据库模型"
sys_logger.info(logmsg)
try:
    # 重命名，与redis统一
    model_mysql_userinfo = UserInfo
    model_mysql_rolepermission = RolePermission
    model_mysql_roleinfo = RoleInfo
    model_mysql_operationinfo = OperationInfo
    model_mysql_useroperationrecord = UserOperationRecord
    model_mysql_functioninfo = FunctionInfo
    model_mysql_functionorg = FunctionOrg
    model_mysql_apiinfo = ApiInfo
    model_mysql_planinfo = PlanInfo
    model_mysql_plantype = PlanType
    model_mysql_taskinfo = TaskInfo
    model_mysql_taskassign = TaskAssign
    model_mysql_workerinfo = WorkerInfo
    model_mysql_tablesnap = TableSnap
    model_mysql_subject = subject

    logmsg = "系统初始化|mysql数据库模型初始化成功"
    sys_logger.debug(logmsg)
except Exception as e:
    logmsg = "系统初始化|mysql数据库模型初始化失败，失败原因：" + repr(e)
    sys_logger.error(logmsg)
    raise RuntimeError(logmsg)
