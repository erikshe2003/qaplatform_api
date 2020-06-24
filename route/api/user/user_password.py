# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_user_password.put import user_password_put


class UserPassword(Resource):
    def put(self):
        return user_password_put()
