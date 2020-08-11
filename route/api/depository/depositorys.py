# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_depositorys.get import key_depositorys_get

class depositorys(Resource):
    def get(self):
        return key_depositorys_get()
