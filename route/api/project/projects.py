# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_projects.get import key_projects_get

class projects(Resource):
    def get(self):
        return key_projects_get()
