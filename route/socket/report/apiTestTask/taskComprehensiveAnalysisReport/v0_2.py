# -*- coding: utf-8 -*-

"""
    返回接口测试的综合分析报告数据-socket路由
    ----校验
            校验传参
            校验账户操作令牌
            校验账户是否存在
            校验账户所属角色是否有操作权限
    ----操作
            接收客户端第一次请求，返回综合分析报告数据，进入轮训等待客户端请求
            轮训接收客户端请求
                1. 客户端请求日志数据，返回综合分析报告数据
                2. 客户端请求断开连接，则关闭连接
"""

import json

from route.socket.report import ws_report
from route.socket import check_parameter, check_token, check_auth, check_user
from handler.pool import mongodb_tasklog_pool
from handler.log import api_logger

from model.mysql import model_mysql_taskinfo
from model.mysql import model_mysql_taskassign


@ws_report.route('taskComprehensiveAnalysisReport.socket')
def task_comprehensive_analysis_report(ws):
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
            ['taskId', int, None, None]
        )
        if not re_json_data:
            api_logger.error('必传参数检查失败')
            ws.send('fail')
            ws.close()
        else:
            api_logger.debug('必传参数检查成功')

        re_task_id = re_json_data['taskId']
        offset = 0
        last_analysis_data = {}
        result_info = []

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
        result_flag, result_info, last_analysis_data, offset = get_running_result(
            re_task_id, snap_data, last_analysis_data, result_info, offset)
        if result_flag:
            api_logger.debug('测试任务:%s综合分析报告数据获取成功' % re_task_id)
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
                        result_flag, result_info, last_analysis_data, offset = get_running_result(
                            re_task_id, snap_data, last_analysis_data, result_info, offset)
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


def get_single_collection(taskid, plugin_id, skip_num):
    try:
        log_query = mongodb_tasklog_pool['task%s_run' % taskid].find(
            {'id': plugin_id},
            {"_id": 0}
        ).skip(skip_num).limit(1)
    except Exception as e:
        api_logger.error("测试任务:%s运行日志数据读取失败，失败原因：%s" % (taskid, repr(e)))
        return False, None
    else:
        api_logger.debug("测试任务:%s运行日志数据读取成功" % taskid)
        return True, list(log_query)


def get_analysis_data(taskid, snap_data, last_analysis_data, last_return_analysis_data, query_offset):
    """
    根据taskId获取运行日志数据
    从上一次查询的末尾开始查询，查询剩余的数据
    每次查询的都是批次数据，且查询出结果后需要替换掉last_analysis_data中相应的值
    如果行数未变化，此时不作请求，本次请求仍旧返回上一次数据
    一共要返回以下数据：
    1.请求记录量count
        查询当前插件的记录的总量
        此数据需累加至last_analysis_data
    2.请求耗时平均值avg
        查询批次记录中耗时t的sum累加值，至last_analysis_data取出t的累加值t_sum，相加后除以当前记录总数算出总体的平均值
        计算后得到的t_sum需要替换掉last_analysis_data中的t_sum值
    3.请求50%位数middle
        得到当前记录总数，然后计算*0.5后的数值并取整得到50%位的偏移量，然后根据此值获取相应位置记录
        此数据无需记录至last_analysis_data
    4.请求90%位数middle
        得到当前记录总数，然后计算*0.9后的数值并取整得到50%位的偏移量，然后根据此值获取相应位置记录
        此数据无需记录至last_analysis_data
    5.请求95%位数middle
        得到当前记录总数，然后计算*0.95后的数值并取整得到50%位的偏移量，然后根据此值获取相应位置记录
        此数据无需记录至last_analysis_data
    6.最小值min
        得到批次记录中t的最小值，然后与last_analysis_data中的min进行比较，并返回更小的值
        如果查询出来的值比last_analysis_data中的更小，则替换之
    7.最大值max
        得到批次记录中t的最大值，然后与last_analysis_data中的max进行比较，并返回更大的值
        如果查询出来的值比last_analysis_data中的更大，则替换之
    8.异常百分比(计算得出)
        查询出批次记录的异常记录量count_err，然后至last_analysis_data中取出异常记录总量，相加后与记录总量进行相除，得出异常百分比
        异常记录量count_err需要至last_analysis_data并取出对应的值并作累加后替换原值
    9.吞吐量(计算得出)
        查询出批次记录中最早的开始时间将之与last_analysis_data中的最早的开始时间进行比较，获得更早的开始时间将之列为测试任务开始时间
        查询出批次记录中最后一条记录的结束时间将之与last_analysis_data中的结束时间进行比较，获得更晚的结束时间将之列为最后一条记录的完成时间
        将(当前记录的总量/结束时间减去开始时间的值)即得到吞吐量
        如果批次记录中最早的开始时间比last_analysis_data中的最早的开始时间更早则替换
        如果批次记录中最晚的结束时间比last_analysis_data中的最晚的结束时间更晚则替换
    10.接收数据量/sec(计算得出)
        查询出批次记录中的返回数据包总量，至last_analysis_data取出返回数据包总量，相加后得到累计返回数据包总量
        将(累计返回数据包总量/结束时间减去开始时间的值)即得到接收接收数据量/sec
        返回数据包总量sum_rsl需要至last_analysis_data并取出对应的值并作累加后替换原值
    11.发送数据量/sec(计算得出)
        查询出批次记录中的发送数据包总量，至last_analysis_data取出发送数据包总量，相加后得到累计发送数据包总量
        将(累计发送数据包总量/结束时间减去开始时间的值)即得到发送数据量/sec
        发送数据包总量sum_rl需要至last_analysis_data并取出对应的值并作累加后替换原值

    :param taskid: 测试任务id，每个测试任务都有对应的snapId
    :param snap_data: 测试任务的快照内容
    :param last_analysis_data: 累计数据值
    :param last_return_analysis_data: 上一次返回内容
    :param query_offset: 分页查询偏移量
    :return:
        True/False-方法执行结果
        analysis_data/None-分析报告数据
        last_analysis_data/None-累加报告值
        offset/-1-下一次查询的偏移量
    """
    analysis_data = []
    try:
        query_count = mongodb_tasklog_pool['task%s_run' % taskid].count()
        # 如果记录无变动，则直接返回上一次的值
        if query_count == query_offset:
            return True, last_return_analysis_data, last_analysis_data, query_offset
        # 查询特殊值
        # 按照插件id分组计算错误的记录量
        special_query_result = list(mongodb_tasklog_pool['task%s_run' % taskid].aggregate([
            {'$skip': query_offset},
            {'$limit': query_count - query_offset},
            {'$match': {'s': False}},
            {'$group': {
                '_id': "$id",
                'count_err': {'$sum': 1}
            }}
        ]))
        # 按照插件id分组计算
        # 最大响应时间
        # 最小响应时间
        # 平均响应时间
        # 请求总数
        # 请求开始时间
        # 请求结束时间
        # 接收数据总量大小
        # 发送数据总量大小
        query_result = list(mongodb_tasklog_pool['task%s_run' % taskid].aggregate([
            {'$skip': query_offset},
            {'$limit': query_count - query_offset},
            {'$group': {
                '_id': "$id",
                'max': {'$max': '$t'},
                'min': {'$min': '$t'},
                't_sum': {'$sum': '$t'},
                'count_all': {'$sum': 1},
                'first_timestamp': {'$min': '$st'},
                'last_timestamp': {'$last': '$et'},
                'rsl': {'$sum': '$rsl'},
                'rl': {'$sum': '$rl'}
            }},
            {'$sort': {'_id': 1}}
        ]))
    except Exception as e:
        api_logger.error("测试任务:%s综合分析数据读取失败，失败原因：%s" % (taskid, repr(e)))
        return False, analysis_data, last_analysis_data, -1
    else:
        api_logger.debug("测试任务:%s综合分析数据读取成功" % taskid)
        # 将特殊值修改为以插件id为key的dict数据类型
        special_query = {}
        for sqr in special_query_result:
            special_query[sqr['_id']] = sqr
        for qr in query_result:
            # 对于尚未记录累加值的，添加统一的累加值模板数据
            if qr['_id'] not in last_analysis_data:
                # 模板中大部分数据均可填充以固定值
                # 准备最小值和最大值
                func_exec, func_return = get_single_collection(taskid, qr['_id'], 0)
                if not func_exec:
                    return False, analysis_data, last_analysis_data, -1
                last_analysis_data[qr['_id']] = {
                    't_sum': 0,
                    'count_all': 0,
                    'min': func_return[0]['t'],
                    'max': func_return[0]['t'],
                    'count_err': 0,
                    'first_timestamp': func_return[0]['st'],
                    'last_timestamp': func_return[0]['et'],
                    'rsl': 0,
                    'rl': 0
                }
            # 准备好待填充的数据
            _id = qr['_id']
            _title = snap_data[qr['_id']]['title']
            # 查询50%位数
            _50_num = int(qr['count_all'] * 0.5)
            func_exec, func_return = get_single_collection(taskid, _id, _50_num)
            if not func_exec:
                return False, analysis_data, last_analysis_data, -1
            _50_t = func_return[0]['t']
            # 查询90%位数
            _90_num = int(qr['count_all'] * 0.9)
            func_exec, func_return = get_single_collection(taskid, _id, _90_num)
            if not func_exec:
                return False, analysis_data, last_analysis_data, -1
            _90_t = func_return[0]['t']
            # 查询95%位数
            _95_num = int(qr['count_all'] * 0.95)
            func_exec, func_return = get_single_collection(taskid, _id, _95_num)
            if not func_exec:
                return False, analysis_data, last_analysis_data, -1
            _95_t = func_return[0]['t']
            # 查询最小值
            if last_analysis_data[_id]['min'] < qr['min']:
                _min = last_analysis_data[_id]['min']
            else:
                _min = qr['min']
                last_analysis_data[_id]['min'] = qr['min']
            # 查询最大值
            if last_analysis_data[_id]['max'] > qr['max']:
                _max = last_analysis_data[_id]['max']
            else:
                _max = qr['max']
                last_analysis_data[_id]['max'] = qr['max']
            # 查询错误率
            if _id in special_query:
                _err_sum = special_query[_id]['count_err'] + last_analysis_data[_id]['count_err']
                # 替换原累加值
                last_analysis_data[_id]['count_err'] = _err_sum
            else:
                _err_sum = last_analysis_data[_id]['count_err']
            # 查询开始及结束时间以计算吞吐量/接收量/发送量
            if last_analysis_data[_id]['first_timestamp'] < qr['first_timestamp']:
                _first_timestamp = last_analysis_data[_id]['first_timestamp']
            else:
                _first_timestamp = qr['first_timestamp']
                last_analysis_data[_id]['first_timestamp'] = qr['first_timestamp']
            if last_analysis_data[_id]['last_timestamp'] > qr['last_timestamp']:
                _last_timestamp = last_analysis_data[_id]['last_timestamp']
            else:
                _last_timestamp = qr['last_timestamp']
                last_analysis_data[_id]['last_timestamp'] = qr['last_timestamp']
            # 查询各项累加值以计算平均值:总量/耗时/接收量/发送量
            _count = qr['count_all'] + last_analysis_data[_id]['count_all']
            _t_sum = qr['t_sum'] + last_analysis_data[_id]['t_sum']
            _rs_sum = qr['rsl'] + last_analysis_data[_id]['rsl']
            _rq_sum = qr['rl'] + last_analysis_data[_id]['rl']
            # 替换原累加值
            last_analysis_data[_id]['count_all'] = _count
            last_analysis_data[_id]['t_sum'] = _t_sum
            last_analysis_data[_id]['rsl'] = _rs_sum
            last_analysis_data[_id]['rl'] = _rq_sum
            # 填充数据
            analysis_data.append({
                'id': _id,
                'title': _title,
                'count_all': _count,
                'count_err': _err_sum,
                'avg': '%.2f' % (_t_sum / _count),
                '50_t': _50_t,
                '90_t': _90_t,
                '95_t': _95_t,
                'min': _min,
                'max': _max,
                'err_percent': '%.2f' % ((_err_sum / _count) * 100),
                'qps_overall': '%.2f' % (_count / ((_last_timestamp - _first_timestamp) / 1000)),
                'qps_estimate': '%.2f' % (1000 / (_t_sum / _count)),
                'first_timestamp': _first_timestamp,
                'last_timestamp': _last_timestamp,
                'rs_per_sec': '%.2f' % ((_rs_sum / 1024) / ((_last_timestamp - _first_timestamp) / 1000)),
                'rq_per_sec': '%.2f' % ((_rq_sum / 1024) / ((_last_timestamp - _first_timestamp) / 1000))
            })
        return True, analysis_data, last_analysis_data, query_count


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


def get_running_result(taskid, snap, last_analysis_data, last_return_analysis_data, query_offset):
    """
    获取数据
    :param taskid: 测试任务id
    :param snap: 测试任务的快照内容
    :param last_analysis_data: 累计数据值
    :param last_return_analysis_data: 上一次返回的内容，用于处理记录无改变时的情况，快速返回结果
    :param query_offset: 数据偏移量
    :return: True/False-方法执行结果，response_json/None-返回值
    """
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {
            "is_running": True,
            "analysis_data": []
        }
    }

    # 获取测试任务执行状态
    func1_excute_result, task_running_status = get_task_running_status(taskid)
    # 如果方法执行失败，直接返回
    if func1_excute_result:
        response_json['data']['is_running'] = task_running_status
    else:
        return False, None, last_analysis_data, -1

    # 获取测试任务执行日志
    func2_excute_result, task_analysis_data, last_analysis_data, offset = get_analysis_data(
        taskid, snap, last_analysis_data, last_return_analysis_data, query_offset)
    # 如果方法执行失败，直接返回
    if func2_excute_result:
        response_json['data']['analysis_data'] = task_analysis_data
    else:
        return False, None, last_analysis_data, -1

    # 最终返回正确结果
    return True, json.dumps(response_json), last_analysis_data, offset
