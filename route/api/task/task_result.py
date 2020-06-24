# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_task_result.post import task_result_post


class TaskResult(Resource):
    def post(self):
        return task_result_post()
