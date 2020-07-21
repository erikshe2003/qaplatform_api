# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_depository.get import key_depository_get
from .restful_depository.post import key_depository_post

class depository(Resource):
    def get(self):
        return key_depository_get()
    def post(self):
        return key_depository_post()
