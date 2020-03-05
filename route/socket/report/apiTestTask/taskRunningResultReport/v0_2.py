# -*- coding: utf-8 -*-

"""
    按照查询条件返回给用户需要的用例执行结果列表-socket路由
    ----校验
            校验传参
            校验账户操作令牌
            校验账户是否存在
            校验账户所属角色是否有操作权限
    ----操作
            接收客户端请求，针对请求做出不同的处理
            接收客户端第一次请求，返回执行应用状态+用例执行结果数据，进入轮训等待客户端请求
            轮训接收客户端请求
                1. 客户端请求日志数据，返回执行应用状态+用例执行结果数据
                2. 客户端请求断开连接，则关闭连接
"""

import json

from route.socket.report import ws_report
from route.socket import check_parameter, check_token, check_auth, check_user
from handler.pool import mongodb_tasklog_pool
from handler.log import api_logger

from model.mysql import model_mysql_taskinfo
from model.mysql import model_mysql_taskassign


@ws_report.route('taskRunningResultReport.socket')
def task_running_result_report(ws):
    while not ws.closed:
        url = 'taskRunningResultReport.socket'
        api_logger.debug('监听来自客户端的首次请求内容...')
        re_data = ws.receive()
        api_logger.debug('接收到来自客户端的首次请求内容')
        # 校验传参
        re_json_data = check_parameter(
            re_data,
            ['mail', str, None, None],
            ['token', str, None, None],
            ['taskId', int, None, None],
            ['search', int, 1, 3],
            ['per', int, None, None]
        )
        if not re_json_data:
            api_logger.debug('必传参数检查失败')
            ws.send('fail')
            ws.close()
        else:
            api_logger.debug('必传参数检查成功')

        re_task_id = re_json_data['taskId']
        re_search = re_json_data['search']
        re_log_per = re_json_data['per']

        # 校验token
        if not check_token(re_json_data['mail'], re_json_data['token']):
            api_logger.error('测试任务:%stoken检查失败' % re_task_id)
            ws.send('fail')
            ws.close()
        else:
            api_logger.debug('测试任务:%stoken检查成功' % re_task_id)

        # 校验账户状态
        if not check_user(re_json_data['mail']):
            api_logger.error('测试任务:%s账户状态检查失败' % re_task_id)
            ws.send('fail')
            ws.close()
        else:
            api_logger.debug('测试任务:%s账户状态检查成功' % re_task_id)

        # 校验权限
        if not check_auth(re_json_data['mail'], url):
            api_logger.error('测试任务:%s账户权限校验失败' % re_task_id)
            ws.send('fail')
            ws.close()
        else:
            api_logger.debug('测试任务:%s账户权限校验成功' % re_task_id)

        # 获取测试计划内容快照
        # 本方法返回值固定故仅执行一次，结果后续都可以用
        result_flag, snap_data = get_snap_data(re_task_id)
        if not result_flag:
            api_logger.error('测试任务:%s测试插件数据获取失败' % re_task_id)
            ws.send('fail')
            ws.close()
        elif snap_data is None:
            api_logger.error('测试任务:%s测试插件数据为空' % re_task_id)
            ws.send('fail')
            ws.close()
        else:
            api_logger.debug('测试任务:%s测试插件数据获取成功' % re_task_id)

        # 首次返回
        result_flag, result_info = get_running_result(re_task_id, snap_data, re_search, 0, re_log_per)
        if result_flag:
            api_logger.debug('测试任务:%s运行日志获取成功' % re_task_id)
            api_logger.debug('测试任务:%s准备回传首次内容' % re_task_id)
            ws.send(result_info)
            api_logger.debug('测试任务:%s首次内容回传成功' % re_task_id)
            get_flag = True
            while get_flag:
                api_logger.debug('测试任务:%s监听来自客户端的请求...' % re_task_id)
                re_data = ws.receive()
                api_logger.debug('测试任务:%s接收到来自客户端的请求内容' % re_task_id)
                re_json_data = check_parameter(
                    re_data,
                    ['action', str, None, None]
                )
                if not re_json_data:
                    api_logger.error('测试任务:%s轮询时接收数据的必传参数检查失败' % re_task_id)
                    ws.send('fail')
                    get_flag = False
                else:
                    api_logger.debug('测试任务:%s轮询时接收数据的必传参数检查成功' % re_task_id)
                    re_action = re_json_data['action']
                    if re_action == 'get':
                        api_logger.error('测试任务:%s客户端请求轮询数据' % re_task_id)
                        re_json_data = check_parameter(
                            re_data,
                            ['offset', int, None, None]
                        )
                        if not re_json_data:
                            api_logger.error('测试任务:%s轮询时接收数据的必传参数检查失败' % re_task_id)
                            ws.send('fail')
                            get_flag = False
                        else:
                            api_logger.debug('测试任务:%s轮询时接收数据的必传参数检查成功' % re_task_id)
                            re_offset = re_json_data['offset']
                            result_flag, result_info = get_running_result(
                                re_task_id, snap_data, re_search, re_offset, re_log_per)
                            if result_flag:
                                api_logger.debug('测试任务:%s轮询时待返回数据获取成功' % re_task_id)
                                api_logger.debug('测试任务:%s轮询时准备回传轮询内容' % re_task_id)
                                ws.send(result_info)
                                api_logger.debug('测试任务:%s轮询时轮询内容回传成功' % re_task_id)
                            else:
                                ws.send('fail')
                                api_logger.error('测试任务:%s轮询时待返回数据获取失败' % re_task_id)
                                get_flag = False
                    elif re_action == 'close':
                        api_logger.error('测试任务:%s客户端请求关闭连接' % re_task_id)
                        ws.send('bye')
                        get_flag = False
                    else:
                        api_logger.warn('测试任务:%s客户端请求方法暂不支持' % re_task_id)
                        ws.send('bye')
                        get_flag = False
            api_logger.debug('测试任务:%s关闭请求' % re_task_id)
            ws.close()
        else:
            api_logger.error('测试任务:%s运行日志获取失败' % re_task_id)
            ws.send('fail')
            ws.close()


def get_snap_data(taskid):
    """
    根据taskId查询执行的测试计划快照内容
    进行json解析
    将snap数据转换为以id为key值为value的dict
    :param taskid: 测试任务id，每个测试任务都有对应的snapId
    :return: True/False-方法执行成功与否，Dict/None-最终数据
    """
    try:
        task_snap_data = model_mysql_taskinfo.query.filter(
            model_mysql_taskinfo.taskId == taskid
        ).first()
    except Exception as e:
        api_logger.error("测试任务:%s基础数据读取失败，失败原因：%s" % (taskid, repr(e)))
        return False, None
    else:
        api_logger.debug("测试任务:%s基础数据读取成功" % taskid)
        if not task_snap_data:
            return True, None
        else:
            result_data = {}
            try:
                task_snap_data_json = json.loads(task_snap_data.snap)
            except Exception as e:
                api_logger.error("测试任务:%s基础数据json解析失败，失败原因：%s" % (taskid, repr(e)))
                return False, None
            else:
                api_logger.debug("测试任务:%s基础数据json解析成功" % taskid)

                def recurse_to_simple_dict(data):
                    if type(data) is dict and 'id' in data:
                        result_data[data['id']] = {
                            'id': data['id'],
                            'oid': data['originalId'],
                            'title': data['title']
                        }
                        for cr in data['children']:
                            recurse_to_simple_dict(cr)

                recurse_to_simple_dict(task_snap_data_json[0])
                return True, result_data


def get_running_logs(taskid, snap_data, search_kind, query_offset=0, query_limit=200):
    """
    根据taskId获取运行日志数据
    并将测试插件数据和运行日志作结合，最终生成待返回的日志信息
    :param taskid: 测试任务id，每个测试任务都有对应的snapId
    :param search_kind: 查询类型，1为仅失败，2为仅通过，3为全部
    :param snap_data: 测试任务的快照内容
    :param query_offset: 分页查询偏移量
    :param query_limit: 分页查询行数
    :return:
        True/False-方法执行结果
        initLog/None-测试任务日志
        count/None-数据总数
    """
    try:
        if search_kind == 3:
            log_query = mongodb_tasklog_pool['task%s_run' % taskid].find(
                {},
                {"_id": 0}
            ).skip(query_offset).limit(query_limit)
        else:
            log_query = mongodb_tasklog_pool['task%s_run' % taskid].find(
                {'s': False if search_kind == 1 else True},
                {"_id": 0}
            ).skip(query_offset).limit(query_limit)
    except Exception as e:
        api_logger.error("测试任务:%s运行日志数据读取失败，失败原因：%s" % (taskid, repr(e)))
        return False, None, -1
    else:
        api_logger.debug("测试任务:%s运行日志数据读取成功" % taskid)
        log_list = []
        i = query_offset
        for lq in list(log_query):
            lq['title'] = snap_data[lq['id']]['title']
            lq['i'] = i
            i += 1
            log_list.append(lq)
        return True, log_list, log_query.count()


def get_task_running_status(taskid):
    """
    获取测试任务执行状态
    获取分配的所有assign记录(当前测试任务下发逻辑为一个任务仅下发给一台worker)的status
    0推送中，1推送成功，-1推送失败，2任务初始化中，-2任务初始化失败，3任务执行中，-3执行异常，10任务结束
    任何一条assign记录的status为0/1/2/3则可以认为测试任务状态为进行中
    :param taskid: 测试任务id
    :return True/False-方法执行结果, True/False/None-测试任务运行状态
    """
    try:
        # 虽然获取的是全部条目，但当前测试任务下发逻辑为1个任务仅下发至1台执行应用
        task_assign_info_list = model_mysql_taskassign.query.filter(
            model_mysql_taskassign.taskId == taskid
        ).all()
    except Exception as e:
        api_logger.error("测试任务:%s运行状态数据读取失败，失败原因：%s" % (taskid, repr(e)))
        return False, None
    else:
        api_logger.debug("测试任务:%s运行状态数据读取成功" % taskid)
        for tail in task_assign_info_list:
            if tail.status in [0, 1, 2, 3]:
                return True, True
        return True, False


def get_running_result(taskid, snap, search_kind, query_offset, query_log_per):
    """
    获取数据
    :param taskid: 测试任务id
    :param snap: 测试任务的快照内容
    :param search_kind: 查询类型，1为仅失败，2为仅通过，3为全部
    :param query_offset: 数据偏移量
    :param query_log_per: 请求数据量
    :return: True/False-方法执行结果，response_json/None-返回值
    """
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {
            "is_running": True,
            "count": 0,
            "start_index": 0,
            "log": []
        }
    }

    # 获取测试任务执行状态
    func1_excute_result, task_running_status = get_task_running_status(taskid)
    # 如果方法执行失败，直接返回
    if func1_excute_result:
        response_json['data']['is_running'] = task_running_status
    else:
        return False, None

    # 获取测试任务执行日志
    func2_excute_result, task_running_log, log_count = get_running_logs(taskid, snap, search_kind, query_offset, query_log_per)
    # 如果方法执行失败，直接返回
    if func2_excute_result:
        response_json['data']['log'] = task_running_log
        response_json['data']['count'] = log_count
        response_json['data']['start_index'] = query_offset
    else:
        return False, None

    # 最终返回正确结果
    return True, json.dumps(response_json)
