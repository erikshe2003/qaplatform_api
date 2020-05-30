# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_user_status.put import user_status_put


class UserStatus(Resource):
    def put(self):
        return user_status_put()
