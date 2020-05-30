# -*- coding: utf-8 -*-


from flask_restful import Resource


from .role_list_restful.get import role_list_get


class RoleList(Resource):
    def get(self):
        return role_list_get()
