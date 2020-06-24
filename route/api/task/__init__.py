# -*- coding: utf-8 -*-

from flask import Blueprint
from flask_restful import Api

from .worker import Worker
from .task import Task
from .task_list import TaskList
from .task_result import TaskResult

api_task = Blueprint('api_task', __name__)
api = Api(api_task)
api.add_resource(Worker, '/worker.json')
api.add_resource(Task, '/task.json')
api.add_resource(TaskList, '/taskList.json')
api.add_resource(TaskResult, '/taskResult.json')
