# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_plan_worktable_snap.get import plan_worktable_snap_get
from .restful_plan_worktable_snap.post import plan_worktable_snap_post


class PlanWorktableSnap(Resource):
    def get(self):
        return plan_worktable_snap_get()

    def post(self):
        return plan_worktable_snap_post()
