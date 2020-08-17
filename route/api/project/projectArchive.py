# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_projectArchive.post import key_projectArchive_post

class projectArchive(Resource):

    def post(self):
        return key_projectArchive_post()
