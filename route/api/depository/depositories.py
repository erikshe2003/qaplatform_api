# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_depositories.get import key_depositories_get


class Depositories(Resource):
    def get(self):
        return key_depositories_get()
