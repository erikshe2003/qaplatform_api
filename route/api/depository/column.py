# -*- coding: utf-8 -*-


from flask_restful import Resource
from .restful_column.get import key_column_get
from .restful_column.post import key_column_post
from .restful_column.put import key_column_put
from .restful_column.delete import key_column_delete
class column(Resource):
    def get(self):
        return key_column_get()
    def post(self):
        return key_column_post()
    def put(self):
        return key_column_put()
    def delete(self):
        return key_column_delete()