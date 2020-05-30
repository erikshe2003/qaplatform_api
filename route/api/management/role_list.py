# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_role_list.get import role_list_get


class RoleList(Resource):
    def get(self):
        return role_list_get()
