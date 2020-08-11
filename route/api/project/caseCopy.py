# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_case_copy.post import key_casecopy_post

class casecopy(Resource):

    def post(self):
        return key_casecopy_post()
