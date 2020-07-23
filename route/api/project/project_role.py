# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_project_role.get import key_projectrole_get

class projectrole(Resource):
    def get(self):
        return key_projectrole_get()
