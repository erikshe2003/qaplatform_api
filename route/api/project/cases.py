# -*- coding: utf-8 -*-


from flask_restful import Resource
from .restful_cases.get import key_cases_get

class cases(Resource):
    def get(self):
        return key_cases_get()
