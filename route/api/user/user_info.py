# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_user_info.get import user_info_get


class UserInfo(Resource):
    def get(self):
        return user_info_get()
