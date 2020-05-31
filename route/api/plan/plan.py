# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_plan.get import plan_get
from .restful_plan.post import plan_post
from .restful_plan.delete import plan_delete


class Plan(Resource):
    def post(self):
        return plan_post()

    def delete(self):
        return plan_delete()

    def get(self):
        return plan_get()
