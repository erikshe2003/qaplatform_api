# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_key_action_code.get import key_action_code_get


class KeyActionCode(Resource):
    def get(self):
        return key_action_code_get()
