# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_exportArchive.get import key_exportArchive_get

class exportArchive(Resource):

    def get(self):
        return key_exportArchive_get()
