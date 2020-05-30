# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_user_list.get import user_list_get


class UserList(Resource):
    def get(self):
        return user_list_get()
