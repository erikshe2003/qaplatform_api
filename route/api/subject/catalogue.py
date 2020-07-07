# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_subject_catalogue.get import key_catalogue_get
from .restful_subject_catalogue.post import key_catalogue_post
from .restful_subject_catalogue.put import key_catalogue_put
from .restful_subject_catalogue.delete import key_catalogue_delete

class catalogue(Resource):
    def get(self):
        return key_catalogue_get()
    def post(self):
        return key_catalogue_post()
    def put(self):
        return key_catalogue_put()
    def delete(self):
        return key_catalogue_delete()
