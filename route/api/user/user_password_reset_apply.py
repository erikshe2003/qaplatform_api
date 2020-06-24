# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_user_password_reset_apply.post import user_password_reset_apply_post


class UserPasswordResetApply(Resource):
    def post(self):
        return user_password_reset_apply_post()
