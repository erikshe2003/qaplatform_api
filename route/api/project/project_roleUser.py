# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_project_roleUser.get import key_projectroleUser_get

class projectroleUser(Resource):
    def get(self):
        return key_projectroleUser_get()
