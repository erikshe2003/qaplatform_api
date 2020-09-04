# -*- coding: utf-8 -*-

"""
    统计时间段内每个请求的各类请求耗时-socket接口
    ----校验
            校验传参
            校验账户操作令牌
            校验账户是否存在
            校验账户所属角色是否有操作权限
    ----操作
            接收客户端请求，针对请求做出不同的处理
            接收客户端第一次请求，按照历史数据计算每个插件的每个时间段的响应时间平均值/最小值/最大值，
            轮训接收客户端请求
                1. 客户端请求日志数据，返回综合分析报告数据
                2. 客户端请求断开连接，则关闭连接
"""

import json
import time
import random
import route.socket
import copy

from sqlalchemy import and_
from operator import itemgetter

from route.socket import check_parameter, check_token, check_user, check_auth
from handler.pool import mongodb_tasklog_pool
from route.socket.report import ws_report
from handler.log import api_logger

from model.mysql import model_mysql_taskinfo
from model.mysql import model_mysql_taskassign


@ws_report.route('timeConsumingAnalysis.socket')
def time_consuming_analysis(ws):
    while not ws.closed:
        url = 'timeConsumingAnalysis.socket'
        api_logger.debug('监听来自客户端的首次请求内容...')
        re_data = ws.receive()
        api_logger.debug('接收到来自客户端的首次请求内容')
        # 校验传参
        re_json_data = check_parameter(
            re_data,
            ['mail', str, None, None],
            ['token', str, None, None],
            ['taskId', int, None, None],
            ['interval', int, None, None],
            ['type', int, 0, None]
        )
        if not re_json_data:
            api_logger.debug('必传参数检查失败')
            ws.send('fail')
            ws.close()
            return False
        else:
            api_logger.debug('必传参数检查成功')

        re_mail = re_json_data['mail']
        re_token = re_json_data['token']
        re_task_id = re_json_data['taskId']
        re_interval = re_json_data['interval']
        re_type = re_json_data['type']

        re_last = 0
        re_start_time = ''
        re_start_time_stamp = 0
        re_end_time = ''
        re_end_time_stamp = 0

        # 校验token
        if not check_token(re_mail, re_token):
            api_logger.warn('测试任务:%stoken检查失败' % re_task_id)
            ws.send('fail')
            ws.close()
            return False
        else:
            api_logger.debug('测试任务:%stoken检查成功' % re_task_id)

        # 校验账户状态
        if not check_user(re_json_data['mail']):
            api_logger.warn('测试任务:%s账户状态检查失败' % re_task_id)
            ws.send('fail')
            ws.close()
            return False
        else:
            api_logger.debug('测试任务:%s账户状态检查成功' % re_task_id)

        # 校验权限
        if not check_auth(re_json_data['mail'], url):
            api_logger.warn('测试任务:%s账户权限校验失败' % re_task_id)
            ws.send('fail')
            ws.close()
            return False
        else:
            api_logger.debug('测试任务:%s账户权限校验成功' % re_task_id)

        # 根据type继续检查传参
        if re_type in [0, 1, 2, 3]:
            re_last = {0: 30, 1: 60, 2: 300, 3: 1800}[re_type]
            # 校验传参
            re_json_data = check_parameter(
                re_data,
                ['last', int, 30, None]
            )
            if not re_json_data:
                api_logger.debug('必传参数检查失败')
                ws.send('fail')
                ws.close()
                return False
            else:
                api_logger.debug('必传参数检查成功')
            result_flag, result_data = get_the_last_log_finish_time(re_task_id)
            if not result_flag:
                api_logger.error('测试任务:%s末条运行日志数据获取失败' % re_task_id)
                ws.send('fail')
                ws.close()
                return False
            else:
                api_logger.debug('测试任务:%s末条运行日志数据获取成功' % re_task_id)
            # 获取任务最后一条log的完成时间获得时间间隔的右边界
            re_end_time_stamp = result_data
            # 倒推获得时间间隔的左边界
            re_start_time_stamp = re_end_time_stamp - re_last * 1000
        else:
            re_json_data = check_parameter(
                re_data,
                ['start', str, None, None],
                ['end', str, None, None]
            )
            if not re_json_data:
                api_logger.debug('必传参数检查失败')
                ws.send('fail')
                ws.close()
                return False
            else:
                api_logger.debug('必传参数检查成功')
            # 校验开始和结束时间
            try:
                re_start_time = re_json_data['start']
                re_end_time = re_json_data['end']
                re_start_time_stamp = int(time.mktime(time.strptime(re_start_time, "%Y-%m-%d %H:%M:%S"))) * 1000
                re_end_time_stamp = int(time.mktime(time.strptime(re_end_time, "%Y-%m-%d %H:%M:%S"))) * 1000
            except Exception as e:
                api_logger.warn('测试任务:%s时间参数传递非法:%s' % (re_task_id, repr(e)))
                ws.send('fail')
                ws.close()
                return False
            else:
                if re_start_time_stamp >= re_end_time_stamp:
                    api_logger.warn('测试任务:%s时间参数传递非法:开始日期大于等于结束日期' % re_task_id)
                    ws.send('fail')
                    ws.close()
                    return False
                else:
                    api_logger.debug('测试任务:%s时间参数传递合法' % re_task_id)

        # 获取测试计划内容快照
        # 本方法返回值固定故仅执行一次，结果后续都可以用
        result_flag, snap_data = get_snap_data(re_task_id)
        if not result_flag:
            api_logger.error('测试任务:%s测试插件数据获取失败' % re_task_id)
            ws.send('fail')
            ws.close()
            return False
        elif snap_data is None:
            api_logger.warn('测试任务:%s测试插件数据为空' % re_task_id)
            ws.send('fail')
            ws.close()
            return False
        else:
            api_logger.debug('测试任务:%s测试插件数据获取成功' % re_task_id)

        # 首次返回
        result_flag, result_info = get_running_result(
            re_task_id,
            snap_data,
            interval=re_interval,
            start=re_start_time_stamp,
            end=re_end_time_stamp
        )
        if result_flag:
            api_logger.debug('测试任务:%s运行日志获取成功' % re_task_id)
            api_logger.debug('测试任务:%s准备回传首次内容' % re_task_id)
            ws.send(result_info)
            api_logger.debug('测试任务:%s首次内容回传成功' % re_task_id)
            msg = ''
            while True:
                api_logger.debug('测试任务:%s监听来自客户端的请求...' % re_task_id)
                re_data = ws.receive()
                api_logger.debug('测试任务:%s接收到来自客户端的请求内容' % re_task_id)
                re_json_data = check_parameter(
                    re_data,
                    ['action', str, None, None]
                )
                if not re_json_data:
                    api_logger.error('测试任务:%s轮询时接收数据的必传参数检查失败' % re_task_id)
                    break
                else:
                    api_logger.debug('测试任务:%s轮询时接收数据的必传参数检查成功' % re_task_id)
                    re_action = re_json_data['action']
                    if re_action == 'get':
                        api_logger.error('测试任务:%s客户端请求轮询数据' % re_task_id)
                        re_json_data = check_parameter(
                            re_data,
                            ['interval', int, None, None],
                            ['type', int, None, None]
                        )
                        if not re_json_data:
                            api_logger.error('测试任务:%s轮询时接收数据的必传参数检查失败' % re_task_id)
                            break
                        else:
                            api_logger.debug('测试任务:%s轮询时接收数据的必传参数检查成功' % re_task_id)

                        re_interval = re_json_data['interval']
                        re_type = re_json_data['type']

                        re_last = 0
                        re_start_time = ''
                        re_start_time_stamp = 0
                        re_end_time = ''
                        re_end_time_stamp = 0

                        # 根据type继续检查传参
                        if re_type in [0, 1, 2, 3]:
                            re_last = {0: 30, 1: 60, 2: 300, 3: 1800}[re_type]
                            # 校验传参
                            re_json_data = check_parameter(
                                re_data,
                                ['last', int, 30, None]
                            )
                            if not re_json_data:
                                api_logger.error('测试任务:%s轮询时必传参数检查失败' % re_task_id)
                                break
                            else:
                                api_logger.debug('测试任务:%s轮询时必传参数检查成功' % re_task_id)
                            result_flag, result_data = get_the_last_log_finish_time(re_task_id)
                            if not result_flag:
                                api_logger.error('测试任务:%s末条运行日志数据获取失败' % re_task_id)
                                break
                            else:
                                api_logger.debug('测试任务:%s末条运行日志数据获取成功' % re_task_id)
                            # 获取任务最后一条log的完成时间获得时间间隔的右边界
                            re_end_time_stamp = result_data
                            # 倒推获得时间间隔的左边界
                            re_start_time_stamp = re_end_time_stamp - re_last * 1000
                        else:
                            re_json_data = check_parameter(
                                re_data,
                                ['start', str, None, None],
                                ['end', str, None, None]
                            )
                            if not re_json_data:
                                api_logger.debug('测试任务:%s轮询时必传参数检查失败' % re_task_id)
                                break
                            else:
                                api_logger.debug('测试任务:%s轮询时必传参数检查成功' % re_task_id)
                            # 校验开始和结束时间
                            try:
                                re_start_time_stamp = int(
                                    time.mktime(time.strptime(re_start_time, "%Y-%m-%d %H:%M:%S")))
                                re_end_time_stamp = int(time.mktime(time.strptime(re_end_time, "%Y-%m-%d %H:%M:%S")))
                            except Exception as e:
                                api_logger.warn('测试任务:%s时间参数传递非法:%s' % (re_task_id, repr(e)))
                                break
                            else:
                                if re_start_time_stamp >= re_end_time_stamp:
                                    api_logger.warn('测试任务:%s时间参数传递非法:开始日期大于等于结束日期' % re_task_id)
                                    break
                                else:
                                    api_logger.debug('测试任务:%s时间参数传递合法' % re_task_id)

                        result_flag, result_info = get_running_result(
                            re_task_id,
                            snap_data,
                            interval=re_interval,
                            start=re_start_time_stamp,
                            end=re_end_time_stamp
                        )
                        if result_flag:
                            api_logger.debug('测试任务:%s轮询时待返回数据获取成功' % re_task_id)
                            api_logger.debug('测试任务:%s轮询时准备回传轮询内容' % re_task_id)
                            ws.send(result_info)
                            api_logger.debug('测试任务:%s轮询时轮询内容回传成功' % re_task_id)
                        else:
                            api_logger.error('测试任务:%s轮询时待返回数据获取失败' % re_task_id)
                            break
                    elif re_action == 'close':
                        api_logger.debug('测试任务:%s客户端请求关闭连接' % re_task_id)
                        break
                    else:
                        api_logger.warn('测试任务:%s客户端请求方法暂不支持' % re_task_id)
                        break
            api_logger.debug('测试任务:%s关闭请求' % re_task_id)
            ws.send('fail')
            ws.close()
            return False
        else:
            api_logger.error('测试任务:%s运行日志获取失败' % re_task_id)
            ws.send('fail')
            ws.close()
            return False


def get_snap_data(taskid):
    """
    根据taskId查询执行的测试计划快照内容
    进行json解析
    将snap数据转换为以id为key值为value的dict，转换时过滤掉无log的插件
    存在log的插件id为：9-MYSQL请求/10-Redis请求/11-HTTP/HTTPS请求
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
                        if data['originalId'] in [9, 10, 11]:
                            result_data[data['id']] = {
                                'id': data['id'],
                                'oid': data['originalId'],
                                'title': data['title']
                            }
                        for cr in data['children']:
                            recurse_to_simple_dict(cr)

                recurse_to_simple_dict(task_snap_data_json[0])
                return True, result_data


def get_the_last_log_finish_time(taskid):
    """
    根据taskId获取运行日志中最后一条的结束时间
    :param taskid: 测试任务id，每个测试任务都有对应的snapId
    :return:
        True/False-方法执行结果
        int/None-结束时间戳
    """
    try:
        log_query = mongodb_tasklog_pool['task%s_run' % taskid].find_one({}, sort=[('_id', -1)])
    except Exception as e:
        api_logger.error("测试任务:%s运行日志数据读取失败，失败原因：%s" % (taskid, repr(e)))
        return False, None
    else:
        api_logger.debug("测试任务:%s运行日志数据读取成功" % taskid)
        return True, log_query['et']


def get_history_consuming_time_report(taskid, snap_data, interval, starttime, endtime):
    """
    根据taskId获取运行日志数据
    并将测试插件数据和运行日志作结合，最终生成待返回的日志信息
    :param taskid: 测试任务id，每个测试任务都有对应的snapId
    :param snap_data: 测试任务的快照内容
    :param interval: 指定时间区隔，为秒数
    :param starttime: 查询起始时间，为保证接口性能，业务上统计时间段或者开始/结束时间二者必填其一，未填则为None
    :param endtime: 查询结束时间，业务上统计时间段或者开始/结束时间二者必填其一，未填则为None
    :return:
        True/False-方法执行结果
        reportData/None-分析报告
    """
    try:
        """
        1.查询所有插件的区分时间段的统计数据分组计算
        db.getCollection('task615_run').aggregate([
            {"$skip": 10000},
            {"$limit": 10000},
            {"$group": {
                "_id": {
                    "pid": "$id",
                    "et": {
                        "$subtract": [
                            "$et",
                            {"$mod": [
                                "$et",
                                1000 * 5 /*聚合时间段，5s*/
                            ]}
                        ]
                    }
                },
                "avg": {"$avg": "$t"},
                "min": {"$min": "$t"},
                "max": {"$max": "$t"},
                "count": {"$sum": 1},
            }},
            {"$project": {
                "_id": 0,
                "pid": "$_id.pid",
                "et": "$_id.et",
                "avg_floor": {"$floor": "$avg"},
                "min": 1,
                "max": 1,
                "count":1
            }},
            {"$sort": {
                "et": -1,
                "pid": 1
            }}
        ])
        2.查询单个插件的区分时间段的统计数据分组计算          
        db.getCollection('task615_run').aggregate([
            {"$skip": 10000},
            {"$limit": 10000},
            {"$match": {"id": 4}},
            {"$group": {
                "_id": {
                    "pid": "$id",
                    "et": {
                        "$subtract": [
                            "$et",
                            {"$mod": [
                                "$et",
                                1000 * 5 /*聚合时间段，5s*/
                            ]}
                        ]
                    }
                },
                "avg": {"$avg": "$t"},
                "min": {"$min": "$t"},
                "max": {"$max": "$t"},
                "count": {"$sum": 1},
            }},
            {"$project": {
                "_id": 0,
                "et": "$_id.et",
                "avg_floor": {"$floor": "$avg"},
                "min": 1,
                "max": 1,
                "count": 1
            }}
        ])
        """
        # 根据会有log的插件id，依次查询其统计结果并填充
        match_condition = {"$match": {"id": 0, "et": {}}}
        if starttime:
            match_condition["$match"]['et']["$gte"] = starttime
        if endtime:
            match_condition["$match"]['et']["$lte"] = endtime
        analysis_report = {}
        for sd in snap_data:
            match_condition["$match"]["id"] = sd
            analysis_report_qurey = list(mongodb_tasklog_pool['task%s_run' % taskid].aggregate([
                match_condition,
                {"$group": {
                    "_id": {
                        "pid": "$id",
                        "et": {
                            "$subtract": [
                                "$et",
                                {"$mod": [
                                    "$et",
                                    1000 * interval  # 聚合时间段
                                ]}
                            ]
                        }
                    },
                    "avg": {"$avg": "$t"},
                    "min": {"$min": "$t"},
                    "max": {"$max": "$t"},
                }},
                {"$project": {
                    "_id": 0,
                    "et": "$_id.et",
                    "avg_floor": {"$floor": "$avg"},
                    "min": 1,
                    "max": 1,
                    "count": 1
                }}
            ]))
            analysis_report_qurey = sorted(analysis_report_qurey, key=itemgetter('et'))
            analysis_report_qurey_time = [time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(arq['et'] / 1000)) for arq in analysis_report_qurey]
            analysis_report_qurey_avg = [arq['avg_floor'] for arq in analysis_report_qurey]
            analysis_report_qurey_min = [arq['min'] for arq in analysis_report_qurey]
            analysis_report_qurey_max = [arq['max'] for arq in analysis_report_qurey]
            snap_data[sd]['log'] = {
                'time': analysis_report_qurey_time,
                'avg': analysis_report_qurey_avg,
                'min': analysis_report_qurey_min,
                'max': analysis_report_qurey_max
            }
            analysis_report[sd] = {
                "id": sd,
                "oid": snap_data[sd]['oid'],
                "title": snap_data[sd]['title'],
                "log": snap_data[sd]['log']
            }
    except Exception as e:
        api_logger.error("测试任务:%s耗时分析数据读取失败，失败原因：%s" % (taskid, repr(e)))
        return False, None
    else:
        api_logger.debug("测试任务:%s耗时分析数据读取成功" % taskid)
        return True, analysis_report


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


def get_running_result(taskid, snap, interval, start=None, end=None):
    """
    获取数据
    :param taskid: 测试任务id
    :param snap: 测试任务的快照内容
    :param interval: 指定时间间隔
    :param start: 开始时间，时间戳，非必填，但start及end至少填一个
    :param end: 结束时间，时间戳，非必填，但start及end至少填一个
    :return: True/False-方法执行结果，response_json/None-返回值
    """
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "操作成功",
        "data": {
            "is_running": True,
            "all_logs": {}
        }
    }

    # 获取测试任务执行状态
    func1_excute_result, task_running_status = get_task_running_status(taskid)
    # 如果方法执行失败，直接返回
    if func1_excute_result:
        response_json['data']['is_running'] = task_running_status
    else:
        return False, None

    # 获取测试任务各个插件的历史响应时间分析报告数据
    func2_excute_result, history_consuming_time_report = get_history_consuming_time_report(
        taskid, snap, interval, start, end)
    # 如果方法执行失败，直接返回
    if func2_excute_result:
        response_json['data']['all_logs'] = history_consuming_time_report
    else:
        return False, None

    # 最终返回正确结果
    return True, json.dumps(response_json)
