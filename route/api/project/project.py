# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_project.post import key_project_post
from .restful_project.get import key_project_get
from .restful_project.put import key_project_put
from .restful_project.delete import key_project_delete
class project(Resource):
    def get(self):
        return key_project_get()
    def post(self):
        return key_project_post()
    def put(self):
        return key_project_put()
    def delete(self):
        return key_project_delete()