# -*- coding: utf-8 -*-


from flask_restful import Resource


from .role_info_list_restful.get import role_info_list_get


class RoleInfoList(Resource):
    def get(self):
        return role_info_list_get()
