# -*- coding: utf-8 -*-

"""
    返回测试任务初始化日志-socket路由
    ----校验
            校验传参
            校验账户操作令牌
            校验账户是否存在
            校验账户所属角色是否有操作权限
    ----操作
            接收客户端请求，针对请求做出不同的处理
            接收客户端第一次请求，返回执行应用状态+初始化日志数据，进入轮训等待客户端请求
            轮训接收客户端请求
                1. 客户端请求日志数据，返回执行应用状态+初始化日志数据
                2. 客户端请求断开连接，则关闭连接
"""

import json

from route.socket.report import ws_report
from route.socket import check_parameter, check_token, check_auth, check_user
from handler.pool import mongodb_tasklog_pool
from handler.log import api_logger

from model.mysql import model_mysql_taskassign


@ws_report.route('taskInitLogReport.socket')
def task_init_log_report(ws):
    while not ws.closed:
        url = 'taskInitLogReport.socket'
        api_logger.debug('监听来自客户端的首次请求内容...')
        re_data = ws.receive()

        api_logger.debug('接收到来自客户端的首次请求内容')
        # 校验传参
        re_json_data = check_parameter(
            re_data,
            ['mail', str, None, None],
            ['token', str, None, None],
            ['taskId', int, None, None],
            ['per', int, None, None]
        )

        if not re_json_data:
            api_logger.error('必传参数检查失败')
            ws.send('fail')
            ws.close()
        else:
            api_logger.debug('必传参数检查成功')

        re_task_id = re_json_data['taskId']
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

        # 首次返回
        result_flag, result_info = get_running_result(re_task_id, 0, re_log_per)
        if result_flag:
            api_logger.debug('测试任务:%s初始化日志获取成功' % re_task_id)
            api_logger.debug('测试任务:%s准备回传首次内容' % re_task_id)
            ws.send(result_info)
            api_logger.debug('测试任务:%s首次内容回传成功' % re_task_id)
            get_flag = True
            while get_flag:
                api_logger.debug('测试任务:%s监听来自客户端的轮询请求...' % re_task_id)
                re_data = ws.receive()
                api_logger.debug('测试任务:%s接收到来自客户端的轮询请求内容' % re_task_id)
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
                            result_flag, result_info = get_running_result(re_task_id, re_offset, re_log_per)
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
            api_logger.error('测试任务:%s初始化日志获取失败' % re_task_id)
            ws.send('fail')
            ws.close()


def get_task_running_status(task_id):
    """
    获取测试任务执行状态
    获取分配的所有assign记录(当前测试任务下发逻辑为一个任务仅下发给一台worker)的status
    0推送中，1推送成功，-1推送失败，2任务初始化中，-2任务初始化失败，3任务执行中，-3执行异常，10任务结束
    任何一条assign记录的status为0/1/2/3则可以认为测试任务状态为进行中
    :param task_id: 测试任务id
    :return True/False-方法执行结果, True/False/None-测试任务运行状态
    """
    try:
        # 虽然获取的是全部条目，但当前测试任务下发逻辑为1个任务仅下发至1台执行应用
        task_assign_info_list = model_mysql_taskassign.query.filter(
            model_mysql_taskassign.taskId == task_id
        ).all()
    except Exception as e:
        api_logger.error("测试任务:%s运行状态数据读取失败，失败原因：%s" % (task_id, repr(e)))
        return False, None
    else:
        api_logger.debug("测试任务:%s运行状态数据读取成功" % task_id)
        for tail in task_assign_info_list:
            if tail.status in [0, 1, 2, 3]:
                return True, True
        return True, False


def get_task_init_logs(task_id, query_offset=0, query_limit=200):
    """
    至mongodb中获取re_task_id对应的初始化日志条目，并将条目组装为单个字符串
    顺序获取
    每次获取N条，并记录下当前获取的条目数
    循环请求时仅返回批次数据，之前返回的不再返回，保证接口每批次返回数据较小
    :param task_id: 测试任务id
    :param query_offset: 分页查询偏移量
    :param query_limit: 分页查询行数
    :return:
        True/False-方法执行结果
        initLog/None-测试任务初始化日志
        count/None-数据总数
    """
    try:
        log_query = mongodb_tasklog_pool['task%s_init' % task_id].find(
            {},
            {"_id": 0, "log": 1}
        ).skip(query_offset).limit(query_limit)
    except Exception as e:
        api_logger.error("测试任务:%s初始化日志数据读取失败，失败原因：%s" % (task_id, repr(e)))
        return False, None, -1
    else:
        api_logger.debug("测试任务:%s初始化日志数据读取成功" % task_id)
        log_list = [lq['log'] for lq in list(log_query)]
        return True, log_list, log_query.count()


def get_running_result(task_id, query_offset, query_re_log_per):
    """
    获取数据
    :param task_id: 测试任务id
    :param query_offset: 数据偏移量
    :param query_re_log_per: 请求数据量
    :return: True/False-方法执行结果，response_json/None-返回值
    """
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "操作成功",
        "data": {
            "is_running": True,
            "count": 0,
            "start_index": 0,
            "log": []
        }
    }

    # 获取测试任务执行状态
    func1_excute_result, task_running_status = get_task_running_status(task_id)
    # 如果方法执行失败，直接返回
    if func1_excute_result:
        response_json['data']['is_running'] = task_running_status
    else:
        return False, None

    # 按照旧的在前新的在后的默认排序组成日志数据
    func2_excute_result, task_init_log, log_count = get_task_init_logs(task_id, query_offset, query_re_log_per)
    # 如果方法执行失败，直接返回
    if func2_excute_result:
        response_json['data']['log'] = task_init_log
        response_json['data']['count'] = log_count
        response_json['data']['start_index'] = query_offset
    else:
        return False, None

    # 最终返回正确结果
    return True, json.dumps(response_json)
