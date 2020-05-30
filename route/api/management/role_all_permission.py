# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_role_all_permission.get import role_all_permission_get


class RoleAllPermission(Resource):
    def get(self):
        return role_all_permission_get()
