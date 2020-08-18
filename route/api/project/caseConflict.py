# -*- coding: utf-8 -*-


from flask_restful import Resource
from .restful_caseConflict.get import key_caseConflict_get
from .restful_caseConflict.put import key_caseConflict_put
class caseConflict(Resource):
    def get(self):
        return key_caseConflict_get()

    def put(self):
        return key_caseConflict_put()