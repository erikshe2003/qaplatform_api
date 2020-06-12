# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_user_info.get import user_info_get
from .restful_user_info.put import user_info_put


class UserInfo(Resource):
    def get(self):
        return user_info_get()

    def put(self):
        return user_info_put()
