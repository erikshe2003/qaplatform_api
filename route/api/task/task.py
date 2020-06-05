# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_task.get import task_get


class Task(Resource):
    def get(self):
        return task_get()
