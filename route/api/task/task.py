# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_task.get import task_get
from .restful_task.post import task_post


class Task(Resource):
    def get(self):
        return task_get()

    def post(self):
        return task_post()
