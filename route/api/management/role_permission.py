# -*- coding: utf-8 -*-


from flask_restful import Resource

from .role_permission_restful.get import role_permission_get
from .role_permission_restful.put import role_permission_put


class RolePermission(Resource):
    def get(self):
        return role_permission_get()

    def put(self):
        return role_permission_put()
