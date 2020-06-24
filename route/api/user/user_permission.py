# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_user_permission.get import user_permission_get


class UserPermission(Resource):
    def get(self):
        return user_permission_get()
