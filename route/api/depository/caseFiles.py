# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_caseFiles.get import key_caseFiles_get


class caseFiles(Resource):
    def get(self):
        return key_caseFiles_get()
