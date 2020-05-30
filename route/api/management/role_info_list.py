# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_role_info_list.get import role_info_list_get


class RoleInfoList(Resource):
    def get(self):
        return role_info_list_get()
