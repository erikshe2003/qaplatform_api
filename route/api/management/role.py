# -*- coding: utf-8 -*-


from flask_restful import Resource


from .role_restful.get import role_get
from .role_restful.post import role_post
from .role_restful.delete import role_delete


class Role(Resource):
    def post(self):
        return role_post()

    def delete(self):
        return role_delete()

    def get(self):
        return role_get()
