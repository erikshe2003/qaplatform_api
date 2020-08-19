# -*- coding: utf-8 -*-


from flask_restful import Resource

from .restful_exportReview.get import key_exportReview_get

class exportReview(Resource):

    def get(self):
        return key_exportReview_get()
