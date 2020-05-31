# -*- coding: utf-8 -*-

from flask import Blueprint
from flask_restful import Api

from .plan import Plan
from .plan_list import PlanList
from .plan_base_type_info import PlanBaseTypeInfo
from .plan_worktable_snap import PlanWorktableSnap
from .plan_worktable_snap_plugin import PlanWorktableSnapPlugin
from .plan_worktable_snap_plugin_file import PlanWorktableSnapPluginFile

api_plan = Blueprint('api_plan', __name__)
api = Api(api_plan)
api.add_resource(Plan, '/plan.json')
api.add_resource(PlanList, '/planList.json')
api.add_resource(PlanBaseTypeInfo, '/planBaseTypeInfo.json')
api.add_resource(PlanWorktableSnap, '/planWorktableSnap.json')
api.add_resource(PlanWorktableSnapPlugin, '/planWorktableSnapPlugin.json')
api.add_resource(PlanWorktableSnapPluginFile, '/planWorktableSnapPluginFile.json')
