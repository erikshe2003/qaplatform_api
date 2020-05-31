# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_plan.post import plan_post


class Plan(Resource):
    def post(self):
        return plan_post()
