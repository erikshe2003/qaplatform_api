# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_user_password.put import user_password_put
from .restful_user_password.post import user_password_post


class UserPassword(Resource):
    def put(self):
        return user_password_put()

    def post(self):
        return user_password_post()
