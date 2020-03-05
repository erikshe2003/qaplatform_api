# -*- coding: utf-8 -*-

from flask import Blueprint


api_management_role = Blueprint("api_management_role", __name__)

# 加载具体路由
from .addRole import add_role
from .deleteRole import delete_role
from .getAllRolePermission import get_all_role_permission
from .getRoleList import get_role_list
from .getRolePermission import get_role_permission
from .searchRole import search_role
from .setRolePermission import set_role_permission
from .getRoleInfoList import get_role_info_list
