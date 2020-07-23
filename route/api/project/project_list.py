# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_project_list.get import key_projectlist_get

class projectlist(Resource):
    def get(self):
        return key_projectlist_get()
