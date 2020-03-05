# -*- coding: utf-8 -*-

from flask import Blueprint

api_task = Blueprint('api_task', __name__)

# 加载具体路由
from route.api.task.apiTestPlanTaskConfigurationInfo import api_test_task_configuration_info
from route.api.task.personalApiTestPlanTaskList import personal_api_test_plan_task_list
from route.api.task.registerWorker import worker_register
from route.api.task.stopTestTask import stop_test_task
from route.api.task.testTaskFinished import test_task_finished
from route.api.task.newTestTask import new_test_task
