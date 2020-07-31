# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_case.get import key_case_get

from .restful_case.delete import key_case_delete
class case(Resource):
    def get(self):
        return key_case_get()
    def delete(self):
        return key_case_delete()