# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_subject_catalogues.get import key_catalogues_get
from .restful_subject_catalogues.post import key_catalogues_post

class catalogues(Resource):
    def get(self):
        return key_catalogues_get()
    def post(self):
        return key_catalogues_post()
