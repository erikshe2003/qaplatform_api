# -*- coding: utf-8 -*-

from flask import Blueprint


api_plan = Blueprint("api_plan", __name__)

# 加载具体路由
from route.api.plan.getPersonalPlanList import get_personal_plan_list
from route.api.plan.searchPersonalPlan import search_personal_plan
from route.api.plan.addPersonalPlan import add_personal_plan
from route.api.plan.getPersonalPlanInfo import get_personal_plan_info
from route.api.plan.savePersonalPlanTable import save_personal_plan_table
from route.api.plan.getBasePlanTypeInfo import get_base_plan_type_info
from route.api.plan.getNewestPersonalPlanTableSnap import get_newest_personal_plan_table_snap
from route.api.plan.parameterizeFile import parameterize_file
from route.api.plan.plugin import plugin
from route.api.plan.copyPlugin import copy_plugin
from route.api.plan.deletePersonalApiTestPlan import delete_personal_api_test_plan
