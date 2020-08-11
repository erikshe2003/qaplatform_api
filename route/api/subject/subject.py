# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_subject.get import key_subject_get
from .restful_subject.post import key_subject_post
from .restful_subject.put import key_subject_put
from .restful_subject.delete import key_subject_delete

class subject(Resource):
    def get(self):
        return key_subject_get()
    def post(self):
        return key_subject_post()
    def put(self):
        return key_subject_put()
    def delete(self):
        return key_subject_delete()

