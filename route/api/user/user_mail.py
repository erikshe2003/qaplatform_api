# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_user_mail.put import user_mail_put


class UserMail(Resource):
    def put(self):
        return user_mail_put()
