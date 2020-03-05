# -*- coding: utf-8 -*-

from flask import Blueprint

ws_report = Blueprint('ws_report', __name__)

# 加载具体路由
from route.socket.report.apiTestTask.timeConsumingAnalysis import time_consuming_analysis
from route.socket.report.apiTestTask.taskComprehensiveAnalysisReport import task_comprehensive_analysis_report
from route.socket.report.apiTestTask.taskInitLogReport import task_init_log_report
from route.socket.report.apiTestTask.taskRunningResultReport import task_running_result_report
from route.socket.report.apiTestTask.throughputAnalysis import throughput_analysis
