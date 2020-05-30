# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_role_permission.get import role_permission_get
from .restful_role_permission.put import role_permission_put


class RolePermission(Resource):
    def get(self):
        return role_permission_get()

    def put(self):
        return role_permission_put()
