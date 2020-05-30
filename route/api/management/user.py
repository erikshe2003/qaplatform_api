# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_user.get import user_get
from .restful_user.put import user_put
from .restful_user.delete import user_delete


class User(Resource):
    def get(self):
        return user_get()

    def put(self):
        return user_put()

    def delete(self):
        return user_delete()
