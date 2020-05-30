# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_user.get import user_get


class User(Resource):
    def get(self):
        return user_get()
