# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_caseReview.post import key_caseReview_post

class caseReview(Resource):

    def post(self):
        return key_caseReview_post()
