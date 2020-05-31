# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_plan_list.get import plan_list_get


class PlanList(Resource):
    def get(self):
        return plan_list_get()
