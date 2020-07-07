# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_case.get import key_case_get
from .restful_case.post import key_case_post
from .restful_case.put import key_case_put

class case(Resource):
    def get(self):
        return key_case_get()
    def post(self):
        return key_case_post()
    def put(self):
        return key_case_put()

