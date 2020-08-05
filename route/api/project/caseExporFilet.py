
# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_caseExporFilet.get import key_caseExporFilet_get

class caseExporFilet(Resource):
    def get(self):
        return key_caseExporFilet_get()
