# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_plan_worktable_snap_plugin_file.get import plan_worktable_snap_plugin_file_get
from .restful_plan_worktable_snap_plugin_file.post import plan_worktable_snap_plugin_file_post
from .restful_plan_worktable_snap_plugin_file.delete import plan_worktable_snap_plugin_file_delete


class PlanWorktableSnapPluginFile(Resource):
    def get(self):
        return plan_worktable_snap_plugin_file_get()

    def post(self):
        return plan_worktable_snap_plugin_file_post()

    def delete(self):
        return plan_worktable_snap_plugin_file_delete()
