# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_project_member.get import key_projectmember_get
from .restful_project_member.put import key_projectmember_put
from .restful_project_member.delete import key_projectmember_delete
class projectmember(Resource):
    def get(self):
        return key_projectmember_get()
    def put(self):
        return key_projectmember_put()
    def delete(self):
        return key_projectmember_delete()