# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_task.get import task_get
from .restful_task.post import task_post
from .restful_task.put import task_put


class Task(Resource):
    def get(self):
        return task_get()

    def post(self):
        return task_post()

    def put(self):
        return task_put()
