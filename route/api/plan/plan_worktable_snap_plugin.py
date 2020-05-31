# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_plan_worktable_snap_plugin.delete import plan_worktable_snap_plugin_delete


class PlanWorktableSnapPlugin(Resource):
    def delete(self):
        return plan_worktable_snap_plugin_delete()
