# -*- coding: utf-8 -*-

import json
import route.socket
import random
import time

from sqlalchemy import and_

from route.socket.report import ws_report
from route.socket import check_parameter, check_token, check_auth, check_user
from handler.pool import mysqlpool
from handler.log import api_logger

from model.mysql import model_mysql_taskinfo
from model.mysql import model_mysql_taskassign
from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_plancase
from model.mysql import model_mysql_planstep
from model.mysql import model_mysql_planplugin
from model.redis import modle_redis_tasklog

"""
    按照查询条件返回给用户需要的用例执行结果树-socket路由
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


@ws_report.route('runningResultTree.socket')
def running_result_tree(ws):
    while not ws.closed:
        # 创建一个随机数，用来区分线程
        request_num = random.randint(0, 10000)
        url = 'runningResultTree.socket'
        api_logger.debug(str(request_num) + '|' + url + '|listen first send from client...')
        action = ws.receive()
        api_logger.debug(str(request_num) + '|' + url + '|get first send from client...')
        # 校验传参
        json_action = check_parameter(action, ['mail', str, None, None],
                                      ['token', str, None, None],
                                      ['taskId', int, None, None],
                                      ['search', int, 1, 3])
        if json_action:
            # 校验token
            if check_token(json_action['mail'], json_action['token']):
                # 校验账户状态
                if check_user(json_action['mail']):
                    # 校验权限
                    if check_auth(json_action['mail'], url):
                        taskid = json_action['taskId']
                        search = json_action['search']
                        # 获取用例信息
                        task_info_flag, task_info = get_task_info(taskid)
                        if task_info_flag:
                            result_flag, result_info = get_running_result(taskid, search, task_info[0], task_info[1], task_info[2])
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
                                            search = int(re_get.split(',')[1])
                                            if search not in [1, 2, 3]:
                                                search = 1
                                        except:
                                            search = 1
                                        result_flag, result_info = get_running_result(taskid, search, task_info[0], task_info[1], task_info[2])
                                        if result_flag:
                                            ws.send(result_info)
                                            i += 1
                                        else:
                                            ws.send('fail')
                                            api_logger.debug(str(request_num) + '|' + url + '|异常返回：' + result_info.encode('utf-8').decode('unicode_escape'))
                                            get_flag = False
                                api_logger.debug(str(request_num) + '|' + url + '|connection is closed...')
                                ws.close()
                            else:
                                api_logger.debug(str(request_num) + '|' + url + '|异常返回：' + result_info.encode('utf-8').decode('unicode_escape'))
                                ws.send('fail')
                                ws.close()
                        else:
                            api_logger.debug(str(request_num) + '|' + url + '|异常返回：' + task_info.encode('utf-8').decode('unicode_escape'))
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


# 读取重组用例信息，方便按照用例执行结果树提取信息
def get_task_info(taskid):
    # 根据任务id查询出当前任务的任务信息
    try:
        taskinfo = model_mysql_taskinfo.query.filter(
            model_mysql_taskinfo.taskId == taskid
        ).first()
    except Exception as e:
        api_logger.error(str(taskid) + "的测试任务数据读取失败，失败原因：" + repr(e))
        return False, route.socket.error_msgs['msg_db_error']

    # 任务id不存在
    if taskinfo is None:
        return False, route.socket.error_msgs['msg_no_task']

    vid = taskinfo.versionId
    pid = taskinfo.planId

    # 根据计划id查询当前任务的测试计划信息
    try:
        planinfo = model_mysql_planinfo.query.filter(
            model_mysql_planinfo.planId == pid
        ).first()
    except Exception as e:
        api_logger.error(str(taskid) + "的测试计划数据读取失败，失败原因：" + repr(e))
        return False, route.socket.error_msgs['msg_db_error']

    # 根据版本id查询当前任务的所有用例和步骤信息-暂时不考虑单条用例调试
    try:
        case_list = mysqlpool.session.query(
            model_mysql_plancase.caseId.label('caseId'),
            model_mysql_plancase.caseTitle.label('caseTitle'),
            model_mysql_planstep.stepId.label('stepId'),
            model_mysql_planplugin.title.label('title'),
        ).join(
            model_mysql_planstep,
            model_mysql_plancase.caseId == model_mysql_planstep.caseId
        ).join(
            model_mysql_planplugin,
            model_mysql_planstep.stepId == model_mysql_planplugin.stepId
        ).filter(
            model_mysql_plancase.versionId == vid,
            model_mysql_planplugin.sequence == 0,
            model_mysql_plancase.status == 0,
            model_mysql_planstep.status == 0
        ).all()
    except Exception as e:
        api_logger.error(str(taskid) + "的测试用例数据读取失败，失败原因：" + repr(e))
        return False, route.socket.error_msgs['msg_db_error']

    # 将用例步骤信息转换成字典形式，键值为：stepid，方便按照stepid提取信息
    new_case_list = {}
    step_count = {}
    for case in case_list:
        new_case_list[case.stepId] = case
        if case.caseId in step_count:
            step_count[case.caseId] += 1
        else:
            step_count[case.caseId] = 1

    # 获取每个用例的步骤数量

    return True, [new_case_list, planinfo, step_count]


# 读取执行日志数据，按照查询条件返回给用户需要的用例执行结果树
def get_running_result(taskid, search, new_case_list, planinfo, step_count):
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "操作成功",
        "data": {}
    }

    # 读取taskid对应的执行日志
    # 遍历执行日志，转换日志数据类型为字典，插入新日志列表
    # 新日志列表按照开始执行时间顺序排序，同时间的按照步骤id顺序排序
    tasklog = modle_redis_tasklog.query(taskid)
    # tasklog_list = list(tasklog)
    if not tasklog:
        return True, json.dumps(response_json)

    try:
        new_tasklog_list = list(map(lambda log: json.loads(log), tasklog))
    except Exception as e:
        api_logger.error(repr(e))
        return False, route.socket.error_msgs['msg_db_error']

    new_tasklog_list.sort(key=lambda x: (x['st'], x['stepid']))

    # 遍历新日志列表，按照用例-步骤维度，生成用例执行结果树
    cases_log = cases_log_build(new_tasklog_list, new_case_list)

    # 遍历用例执行结果树，计算步骤的执行结果和用例的执行结果
    case_pass = 0
    case_fail = 0
    for case in cases_log:
        case['start_time'] = case['steps_log'][0]['step_log']['st']
        case['end_time'] = None
        steps = len(case['steps_log'])
        if steps == step_count[case['caseId']]:
            case['end_time'] = case['steps_log'][-1]['step_log']['et']
            case['is_finished'] = True
        else:
            case['is_finished'] = False
        for step in case['steps_log']:
            if step['step_log']['self']['re'] == 0:
                case['steps_fail'] += 1
            else:
                case['steps_pass'] += 1
        if case['is_finished'] == True and case['steps_fail'] > 0:
            case_fail += 1
        elif case['is_finished'] == True and case['steps_fail'] == 0:
            case_pass += 1

    # 按照查询条件返回给用户需要的用例执行结果树
    # 查询失败的用例
    if search == 1:
        i = 0
        while i < len(cases_log):
            if cases_log[i]['is_finished'] == False or (
                    cases_log[i]['is_finished'] == True and cases_log[i]['steps_fail'] == 0):
                cases_log.remove(cases_log[i])
                i -= 1
            i += 1
    # 查询成功的用例
    elif search == 2:
        i = 0
        while i < len(cases_log):
            if cases_log[i]['is_finished'] == False or (
                    cases_log[i]['is_finished'] == True and cases_log[i]['steps_fail'] > 0):
                cases_log.remove(cases_log[i])
                i -= 1
            i += 1

    # 查询当前任务执行状态
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
            running = True

    response_json['data']['cases_log'] = cases_log[-5000:]
    response_json['data']['task_id'] = taskid
    response_json['data']['plan_id'] = planinfo.planId
    response_json['data']['plan_name'] = planinfo.planTitle
    response_json['data']['case_pass'] = case_pass
    response_json['data']['case_fail'] = case_fail
    response_json['data']['start_time'] = new_tasklog_list[0]['st']
    response_json['data']['end_time'] = None if running else new_tasklog_list[-1]['et']

    return True, json.dumps(response_json)


def cases_log_build(new_tasklog_list, new_case_list):
    cases_log = []
    cases_log_unique_id = {}
    for tasklog in new_tasklog_list:
        unique_id = '%d_%d_%d_%d' % (tasklog['wid'], tasklog['uid'], tasklog['sid'], tasklog['cid'])
        if len(cases_log) == 0:
            cases_log_unique_id[unique_id] = 0
            try:
                cases_log.append({
                    'id': unique_id,
                    'caseId': new_case_list[tasklog['stepid']].caseId,
                    'case_name': new_case_list[tasklog['stepid']].caseTitle,
                    'steps_pass': 0,
                    'steps_fail': 0,
                    'steps_log': [{
                        'step_id': tasklog['stepid'],
                        'step_name': new_case_list[tasklog['stepid']].title,
                        'step_log': tasklog
                    }]
                })
            except:
                pass
        else:
            # 判断cases_log_unique_id中是否有unique_id
            if unique_id in cases_log_unique_id:
                try:
                    cases_log[cases_log_unique_id[unique_id]]['steps_log'].append({
                        'step_id': tasklog['stepid'],
                        'step_name': new_case_list[tasklog['stepid']].title,
                        'step_log': tasklog
                    })
                except:
                    pass
            else:
                cases_log_unique_id[unique_id] = len(cases_log)
                try:
                    cases_log.append({
                        'id': unique_id,
                        'caseId': new_case_list[tasklog['stepid']].caseId,
                        'case_name': new_case_list[tasklog['stepid']].caseTitle,
                        'steps_pass': 0,
                        'steps_fail': 0,
                        'steps_log': [{
                            'step_id': tasklog['stepid'],
                            'step_name': new_case_list[tasklog['stepid']].title,
                            'step_log': tasklog}]
                    })
                except:
                    pass

    return cases_log
