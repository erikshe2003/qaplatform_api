# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_plan_worktable_snap_plugin.delete import plan_worktable_snap_plugin_delete
from .restful_plan_worktable_snap_plugin.post import plan_worktable_snap_plugin_post


class PlanWorktableSnapPlugin(Resource):
    def post(self):
        return plan_worktable_snap_plugin_post()

    def delete(self):
        return plan_worktable_snap_plugin_delete()
