# -*- coding: utf-8 -*-


from flask_restful import Resource

from .role_all_permission_restful.get import role_all_permission_get


class RolePermission(Resource):
    def get(self):
        return role_all_permission_get()
