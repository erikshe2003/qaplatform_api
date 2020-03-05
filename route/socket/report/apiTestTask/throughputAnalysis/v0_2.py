# -*- coding: utf-8 -*-

import json
import route.socket
import math
import random
import copy
import numpy
from sqlalchemy import and_

from route.socket.report import ws_report
from route.socket import check_parameter, check_token, check_user, check_auth
from handler.pool import mysqlpool
from handler.log import api_logger

from model.mysql import model_mysql_taskinfo
from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_taskassign
from model.redis import modle_redis_tasklog

"""
    统计时间段内每个请求的吞吐量-socket接口
    ----校验
            校验传参
            校验账户操作令牌
            校验账户是否存在
            校验账户所属角色是否有操作权限
    ----操作
            接收客户端请求，针对请求做出不同的处理
            接收客户端第一次请求，返回用例执行结果，进入轮训等待客户端请求
            轮训接收客户端请求
                1. 客户端请求日志数据，返回用例执行结果
                2. 客户端请求断开连接，则关闭连接
"""


@ws_report.route('throughputAnalysis.socket')
def throughput_analysis(ws):
    while not ws.closed:
        # 创建一个随机数，用来区分线程
        request_num = random.randint(0, 10000)
        url = 'throughputAnalysis.socket'
        api_logger.debug(str(request_num) + '|' + url + '|listen first send from client...')
        action = ws.receive()
        api_logger.debug(str(request_num) + '|' + url + '|get first send from client...')
        # 校验传参
        json_action = check_parameter(action, ['mail', str, None, None],
                                      ['token', str, None, None],
                                      ['taskId', int, None, None],
                                      ['time', int, 1, None])
        if json_action:
            # 校验token
            if check_token(json_action['mail'], json_action['token']):
                # 校验账户状态
                if check_user(json_action['mail']):
                    # 校验权限
                    if check_auth(json_action['mail'], url):
                        taskid = json_action['taskId']
                        time = json_action['time']
                        # 获取用例信息
                        qps_log_flag, qps_log = init_qps_log(taskid)
                        if qps_log_flag:
                            result_flag, result_info = get_throughput(taskid, time, qps_log)
                            if result_flag:
                                ws.send(result_info)
                                get_flag = True
                                i = 2
                                while get_flag:
                                    api_logger.debug(str(request_num) + '|' + url + '|listen send from client...' + str(i))
                                    re_get = ws.receive()
                                    api_logger.debug(str(request_num) + '|' + url + '|get send from client...' + str(i))
                                    if not re_get or 'get' not in re_get:
                                        get_flag = False
                                    else:
                                        try:
                                            time = int(re_get.split(',')[1])
                                            if not time:
                                                time = 1
                                        except:
                                            time = 1
                                        result_flag, result_info = get_throughput(taskid, time, qps_log)
                                        if result_flag:
                                            ws.send(result_info)
                                            i += 1
                                        else:
                                            ws.send('fail')
                                            api_logger.debug(str(request_num) + '|' + url + '|异常返回：' + result_info.encode('utf-8').decode('unicode_escape'))
                                            get_flag = False
                                api_logger.debug(str(request_num) + '|' + url + '|connection is closed normally...')
                                ws.close()
                            else:
                                api_logger.debug(str(request_num) + '|' + url + '|异常返回：' + result_info.encode('utf-8').decode('unicode_escape'))
                                ws.send('fail')
                                ws.close()
                        else:
                            api_logger.debug(str(request_num) + '|' + url + '|异常返回：' + qps_log.encode('utf-8').decode('unicode_escape'))
                            ws.send('fail')
                            ws.close()
                    else:
                        api_logger.debug(str(request_num) + '|' + url + '|check_auth fail...')
                        ws.send('fail')
                        ws.close()
                else:
                    api_logger.debug(str(request_num) + '|' + url + '|check_user fail...')
                    ws.send('fail')
                    ws.close()
            else:
                api_logger.debug(str(request_num) + '|' + url + '|check_token fail...')
                ws.send('fail')
                ws.close()
        else:
            api_logger.debug(str(request_num) + '|' + url + '|check_parameter fail...')
            ws.send('fail')
            ws.close()


# 生成测试步骤的吞吐量空列表
def init_qps_log(taskid):
    # 根据任务id查询出当前任务的任务信息
    try:
        taskinfo = model_mysql_taskinfo.query.filter(
            model_mysql_taskinfo.taskId == taskid
        ).first()
    except Exception as e:
        api_logger.error(str(taskid) + "的测试任务数据读取失败，失败原因：" + repr(e))
        return False, route.socket.error_msgs['msg_db_error']

    # 当任务为调试任务，则不支持查看本报告
    if taskinfo is None or taskinfo.taskType < 3:
        return False, route.socket.error_msgs['msg_tasktype_error']
    vid = taskinfo.versionId
    pid = taskinfo.planId

    # 根据计划id查询当前任务的测试计划类型
    try:
        planinfo = model_mysql_planinfo.query.filter(
            model_mysql_planinfo.planId == pid
        ).first()
    except Exception as e:
        api_logger.error(str(taskid) + "的测试计划数据读取失败，失败原因：" + repr(e))
        return False, route.socket.error_msgs['msg_db_error']

    # 根据版本id查询当前任务的所有用例和步骤
    # try:
    #     case_list = mysqlpool.session.query(
    #         model_mysql_plancase.caseId.label('caseId'),
    #         model_mysql_plancase.caseTitle.label('caseTitle'),
    #         model_mysql_planstep.stepId.label('stepId'),
    #         model_mysql_planplugin.title.label('title'),
    #     ).join(
    #         model_mysql_planstep,
    #         model_mysql_plancase.caseId == model_mysql_planstep.caseId
    #     ).join(
    #         model_mysql_planplugin,
    #         model_mysql_planstep.stepId == model_mysql_planplugin.stepId
    #     ).filter(
    #         model_mysql_plancase.versionId == vid,
    #         model_mysql_planplugin.sequence == 0,
    #         model_mysql_plancase.status == 0,
    #         model_mysql_planstep.status == 0
    #     ).all()
    # except Exception as e:
    #     api_logger.error(str(taskid) + "的测试用例数据读取失败，失败原因：" + repr(e))
    #     return False, route.socket.error_msgs['msg_db_error']
    #
    # # 遍历测试用例数据,生成测试步骤维度列表，qps默认空列表，用于存放各时间段内吞吐量，qps按照时间段顺序排序
    # # 步骤名称格式：用例名称_步骤名称
    # qps_log = [{"stepid": case[2], "name": (case[1] if case[1] else '未填写用例名称') + '_' + (case[3] if case[3] else '未填写步骤名称'), "qps_temp": [], "qps": []} for case in case_list]
    #
    # return True, qps_log


# 读取执行日志，计算吞吐量，存放入吞吐量列表中
def get_throughput(taskid, time, qps):
    qps_log = copy.deepcopy(qps)
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {}
    }

    # 读取taskid对应的执行日志
    # 遍历执行日志，转换日志数据类型为字典，读取需要用到的字段，插入新日志列表
    # 新日志列表按照开始执行时间顺序排序，同时间的按照步骤id顺序排序
    tasklog = modle_redis_tasklog.query(taskid)
    if not tasklog:
        return True, json.dumps(response_json)

    new_tasklog_list = []
    for log in tasklog:
        log_dict = json.loads(str(log, encoding='utf-8'))
        new_tasklog_list.append({
            "caseid": log_dict['cid'],
            "stepid": log_dict['stepid'],
            "et": log_dict['et']})
    new_tasklog_list.sort(key=lambda x: (x['et'], x['stepid']))

    # 按照时间遍历日志列表，计算时间段内每个步骤的吞吐量，加入到qps_log中
    tasklog_count = len(new_tasklog_list)
    first_et = new_tasklog_list[0]['et'] + time
    if tasklog_count == 1:
        last_et = first_et
    else:
        last_et = math.ceil((new_tasklog_list[-1]['et'] - first_et) / time) * time + first_et
    position = 0
    empty = False
    second = 0
    for et in numpy.arange(first_et, last_et + 1, time):
        step_list = {}
        second += time
        for i in range(position, tasklog_count):
            if new_tasklog_list[i]['et'] <= et:
                stepid = new_tasklog_list[i]['stepid']
                if stepid in step_list:
                    step_list[stepid]['count'] += 1
                else:
                    step_list[stepid] = {"count": 1}
            else:
                position = i
                empty = True
                break
        if empty and len(step_list) == 0:
            for log in qps_log:
                if len(log['qps_temp']) > 0:
                    log['qps_temp'].append(log['qps_temp'][-1])
                    log['qps'].append(round(log['qps_temp'][-1] / second, 2))
                else:
                    log['qps_temp'].append(0)
                    log['qps'].append(0)
            empty = False
        else:
            for log in qps_log:
                if log['stepid'] in step_list:
                    if len(log['qps_temp']) > 0:
                        log['qps_temp'].append(step_list[log['stepid']]['count'] + log['qps_temp'][-1])
                        log['qps'].append(round(log['qps_temp'][-1] / second, 2))
                    else:
                        log['qps_temp'].append(step_list[log['stepid']]['count'])
                        log['qps'].append(round(log['qps_temp'][-1] / second, 2))
                else:
                    if len(log['qps_temp']) > 0:
                        log['qps_temp'].append(log['qps_temp'][-1])
                        log['qps'].append(round(log['qps_temp'][-1] / second, 2))
                    else:
                        log['qps_temp'].append(0)
                        log['qps'].append(0)

    for log in qps_log:
        log.pop('qps_temp')

    try:
        mysqlpool.session.commit()
        taskassign = model_mysql_taskassign.query.filter(
            and_(
                model_mysql_taskassign.status.in_((0, 1)),
                model_mysql_taskassign.taskId == taskid
            )
        ).all()
    except Exception as e:
        api_logger.error(str(taskid) + "的任务分配数据读取失败，失败原因：" + repr(e))
        return False, route.socket.error_msgs['msg_db_error']

    running = False

    for data in taskassign:
        if not data.finishTime:
            running = False if running else True

    response_json['data']['task_id'] = taskid
    response_json['data']['starttime'] = first_et
    response_json['data']['interval'] = time
    response_json['data']['qps_log'] = qps_log
    response_json['data']['is_finished'] = False if running else True

    return True, json.dumps(response_json)
