# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_token.post import token_post


class Token(Resource):
    def post(self):
        return token_post()
