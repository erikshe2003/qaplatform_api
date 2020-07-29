# -*- coding: utf-8 -*-


from flask_restful import Resource
from .restful_cases.get import key_cases_get
from .restful_cases.delete import key_cases_delete
from .restful_cases.put import key_cases_put
class cases(Resource):
    def get(self):
        return key_cases_get()
    def delete(self):
        return key_cases_delete()
    def put(self):
        return key_cases_put()