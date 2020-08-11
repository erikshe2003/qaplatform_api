# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_caseEditLog.get import key_caseEditLog_get


class caseEditLog(Resource):
    def get(self):
        return key_caseEditLog_get()
