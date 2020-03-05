# -*- coding: utf-8 -*-

from flask import Blueprint

ws_plan = Blueprint('ws_plan', __name__)

# 加载具体路由
from route.socket.plan.api import syncPersonalApiTestPlanTable
