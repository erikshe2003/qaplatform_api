# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_task_list.get import task_list_get


class TaskList(Resource):
    def get(self):
        return task_list_get()
