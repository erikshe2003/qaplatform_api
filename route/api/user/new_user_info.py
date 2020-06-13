# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_new_user_info.put import new_user_info_put
from .restful_new_user_info.post import new_user_info_post


class NewUserInfo(Resource):
    def put(self):
        return new_user_info_put()

    def post(self):
        return new_user_info_post()
