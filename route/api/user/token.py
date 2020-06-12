# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_token.get import token_get
from .restful_token.post import token_post


class Token(Resource):
    def get(self):
        return token_get()

    def post(self):
        return token_post()
