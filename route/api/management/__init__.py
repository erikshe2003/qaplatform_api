# -*- coding: utf-8 -*-

from flask import Blueprint
from flask_restful import Api

from .role import Role
from .role_list import RoleList
from .role_info_list import RoleInfoList
from .role_permission import RolePermission
from .role_all_permission import RoleAllPermission

from .user_list import UserList

api_management = Blueprint('api_management', __name__)
api = Api(api_management)
api.add_resource(Role, '/role.json')
api.add_resource(RoleList, '/roleList.json')
api.add_resource(RoleInfoList, '/roleInfoList.json')
api.add_resource(RolePermission, '/rolePermission.json')
api.add_resource(RoleAllPermission, '/roleAllPermission.json')

api.add_resource(UserList, '/userList.json')
