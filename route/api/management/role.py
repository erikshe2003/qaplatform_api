# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_role.get import role_get
from .restful_role.post import role_post
from .restful_role.delete import role_delete


class Role(Resource):
    def post(self):
        return role_post()

    def delete(self):
        return role_delete()

    def get(self):
        return role_get()
