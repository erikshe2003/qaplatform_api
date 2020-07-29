# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_case_index.put import key_caseindex_put

class caseindex(Resource):

    def put(self):
        return key_caseindex_put()
