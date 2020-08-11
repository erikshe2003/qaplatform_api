# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_project_column.get import key_projectcolumn_get

class projectcolumn(Resource):
    def get(self):
        return key_projectcolumn_get()