# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_plan_base_type_info.get import plan_base_type_info_get


class PlanBaseTypeInfo(Resource):
    def get(self):
        return plan_base_type_info_get()
