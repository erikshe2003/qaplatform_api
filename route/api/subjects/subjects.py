# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_subjects.get import key_subjects_get

class subjects(Resource):
    def get(self):
        return key_subjects_get()
