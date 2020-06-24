# -*- coding: utf-8 -*-

import json
import datetime
import route.socket

from sqlalchemy import and_

from route.socket import check_parameter, check_token, check_user, check_auth
from route.socket.plan import ws_plan
from handler.pool import mysqlpool
from handler.log import api_logger
from handler.config import appconfig

from model.mysql import model_mysql_tablesnap
from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_userinfo
from model.redis import modle_redis_apitestplanworktable

"""
    与前端打通socket通道，将内容同步至数据库-socket接口
    ----校验
            校验传参
            校验账户操作令牌
            校验账户是否存在
            校验账户所属角色是否有操作权限
    ----操作
            将测试计划的最新快照内容拉取至redis中，并在值中添加时间，用于定时同步至mysql生成新快照
            将测试计划的最新快照内容返回给前端，然后进入监听状态
            一旦收到存储请求，则将redis中对应的值更新掉，并且判断与记录的时间之间是否相差了15min，如果是则在mysql生成新快照。更新时间
            一旦收到关闭请求，则将redis中对应的值同步值mysql生成新快照，并删除redis中的数据
    ----备注
            与前端商议的存储请求间隔是5-10s，生成快照间隔是15min
"""


@ws_plan.route('syncPersonalApiTestPlanTable.socket')
def sync_personal_api_test_plan_table(ws):
    check_flag = True
    url = 'requestTimeConsumingAnalysis.socket'
    while not ws.closed:
        api_logger.debug('syncPersonalApiTestPlanTable|监听获取首次入参...')
        action = ws.receive()
        api_logger.debug('syncPersonalApiTestPlanTable|获取到首次入参')
        # 各种校验
        # 校验传参
        # 首次入参仅要求mail/token/planId
        json_action = check_parameter(
            action,
            ['mail', str, None, None],
            ['token', str, None, None],
            ['planId', int, None, None]
        )
        if check_flag:
            if json_action:
                api_logger.debug('入参检查通过')
            else:
                api_logger.debug('入参检查失败')
                check_flag = False
        # 校验token
        if check_flag:
            if check_token(json_action['mail'], json_action['token']):
                api_logger.debug('token检查通过')
            else:
                api_logger.debug('token检查失败')
                check_flag = False
        # 校验账户状态
        if check_flag:
            if check_user(json_action['mail']):
                api_logger.debug('账户状态检查通过')
            else:
                api_logger.debug('账户状态检查失败')
                check_flag = False
        # 校验权限
        if check_flag:
            if check_auth(json_action['mail'], url):
                api_logger.debug('账户权限检查通过')
            else:
                api_logger.debug('账户权限检查失败')
                check_flag = False
        # 校验计划所有者
        if check_flag:
            if check_owner(json_action['planId'], json_action['mail']):
                api_logger.debug('计划的账户所有者检查通过')
            else:
                api_logger.debug('计划的账户所有者检查失败')
                check_flag = False
        # 根据状态位决定要不要执行
        if check_flag:
            # 首次读取快照内容
            gstd_flag, gstd_table = get_snap_table_data(json_action['planId'])
            if gstd_flag:
                ws.send(json.dumps({
                    "error_code": 200,
                    "error_msg": "首次获取工作台快照内容成功",
                    "action": "get",
                    "data": gstd_table
                }))
                get_flag = True
                while get_flag:
                    api_logger.debug('等待获取请求...')
                    ws_re = ws.receive()
                    # 如果连接强制被断开，则会接收到None
                    if ws_re is not None:
                        api_logger.debug('成功获取请求')
                        # 尝试读取内容
                        try:
                            ws_re_json = json.loads(ws_re)
                        except Exception as e:
                            api_logger.debug('请求内容格式非法:%s' % repr(e))
                            ws.send(json.dumps({
                                "error_code": 201,
                                "error_msg": "请求内容格式非法",
                                "action": "",
                                "data": ""
                            }))
                            get_flag = False
                        else:
                            # 判断传入内容中是否有action，且传入的planId是否与第一次一致
                            if 'action' in ws_re_json and 'planId' in ws_re_json and ws_re_json['planId'] == json_action['planId']:
                                if ws_re_json['action'] == 'set' and 'table' in ws_re_json:
                                    if set_snap_table_data(ws_re_json['planId'], ws_re_json['table']):
                                        api_logger.debug('同步成功')
                                        ws.send(json.dumps({
                                            "error_code": 200,
                                            "error_msg": "同步成功",
                                            "action": "set",
                                            "data": ""
                                        }))
                                    else:
                                        api_logger.debug('同步失败，ws_re_json缺少关键key')
                                        ws.send(json.dumps({
                                            "error_code": 500,
                                            "error_msg": "同步失败，请联系管理员",
                                            "action": "set",
                                            "data": ""
                                        }))
                                        get_flag = False
                                elif ws_re_json['action'] == 'get':
                                    gstd_flag, gstd_table = get_snap_table_data(ws_re_json['planId'])
                                    if gstd_flag:
                                        api_logger.debug('数据获取成功')
                                        ws.send(json.dumps({
                                            "error_code": 200,
                                            "error_msg": "数据获取成功",
                                            "action": "get",
                                            "data": gstd_table
                                        }))
                                    else:
                                        api_logger.debug('数据获取失败')
                                        ws.send(json.dumps({
                                            "error_code": 500,
                                            "error_msg": "数据获取失败，请联系管理员",
                                            "action": "get",
                                            "data": ""
                                        }))
                                        get_flag = False
                                elif ws_re_json['action'] == 'close':
                                    api_logger.debug('ws接口正常关闭')
                                    ws.close()
                                    # 将redis中的数据同步至mysql生成快照
                                    get_flag = False
                                    create_snap_when_close(json_action['planId'])
                                else:
                                    api_logger.debug('请求内容格式非法')
                                    ws.send(json.dumps({
                                        "error_code": 201,
                                        "error_msg": "请求内容格式非法",
                                        "action": "",
                                        "data": ""
                                    }))
                                    get_flag = False
                            else:
                                api_logger.debug('请求内容格式非法')
                                ws.send(json.dumps({
                                    "error_code": 201,
                                    "error_msg": "请求内容格式非法",
                                    "action": "",
                                    "data": ""
                                }))
                                get_flag = False
                    else:
                        api_logger.debug('ws接口被强制关闭')
                        ws.close()
                        # 将redis中的数据同步至mysql生成快照
                        get_flag = False
                        create_snap_when_close(json_action['planId'])
            else:
                ws.send(json.dumps({
                    "error_code": 500,
                    "error_msg": "首次获取工作台快照内容失败，请联系管理员",
                    "action": "get",
                    "data": ""
                }))
                api_logger.error('首次获取工作台快照内容失败')
                ws.close()
        else:
            ws.send(json.dumps({
                "error_code": 201,
                "error_msg": "入参校验失败",
                "action": "get",
                "data": ""
            }))
            api_logger.debug('入参校验失败')
            ws.close()


def check_owner(plan_id, mail):
    # 查询测试计划基础信息，并取出所属者账户id
    try:
        mysql_plan_info = model_mysql_planinfo.query.filter(
            model_mysql_planinfo.planId == plan_id
        ).first()
    except Exception as e:
        api_logger.error("model_mysql_planinfo数据读取失败，失败原因：" + repr(e))
        return None, route.error_msgs[500]['msg_db_error']
    else:
        if mysql_plan_info is None:
            return None, route.error_msgs[201]['msg_no_plan']
        else:
            plan_user_id = mysql_plan_info.ownerId

    # 查询账户信息，并取出账户id
    try:
        mysql_userinfo = model_mysql_userinfo.query.filter(
            model_mysql_userinfo.userEmail == mail
        ).first()
        api_logger.debug("model_mysql_userinfo数据读取成功")
    except Exception as e:
        api_logger.error("model_mysql_userinfo数据读取失败，失败原因：" + repr(e))
        return None, route.error_msgs[500]['msg_db_error']
    else:
        if mysql_userinfo is None:
            return None, route.error_msgs[201]['msg_no_user']
        else:
            request_user_id = mysql_userinfo.userId

    # 如果操作者和计划拥有者不是同一人，则报错
    if plan_user_id != request_user_id:
        return False, None
    else:
        return True, None


def get_snap_table_data(plan_id):
    # 于redis中尝试读取计划的快照缓存
    cache_table_bytes = modle_redis_apitestplanworktable.query_table(plan_id=plan_id)
    # 如果缓存中没有，就去mysql读取并且同步至redis
    if cache_table_bytes is None:
        # 读取mysql中对应plan的最新snap
        try:
            mysql_snap_data = model_mysql_tablesnap.query.filter(
                and_(
                    model_mysql_tablesnap.planId == plan_id,
                    model_mysql_tablesnap.status == 1
                )
            ).order_by(
                model_mysql_tablesnap.id.desc()
            ).limit(1).first()
            api_logger.debug("model_mysql_tablesnap数据读取成功")
        except Exception as e:
            api_logger.error("model_mysql_tablesnap数据读取失败，失败原因：" + repr(e))
            return False, None
        else:
            if mysql_snap_data:
                # 如果查询到了，则同步至redis
                redis_set_flag = True
                redis_set_flag = modle_redis_apitestplanworktable.set_table(plan_id, mysql_snap_data.table)
                redis_set_flag = modle_redis_apitestplanworktable.set_time(plan_id)
                if redis_set_flag:
                    return True, mysql_snap_data.table
                else:
                    return False, None
            else:
                # 如果无记录，说明是新测试计划，此时需要在mysql中新增空记录，然后一并同步至redis
                # 新增status为1的snap，内容为空
                new_blank_snap = model_mysql_tablesnap(
                    status=1,
                    planId=plan_id,
                    snapAddTime=datetime.datetime.now(),
                    table="[]"
                )
                try:
                    mysqlpool.session.add(new_blank_snap)
                    mysqlpool.session.commit()
                except Exception as e:
                    api_logger.error("new_blank_snap数据写入失败，失败原因：" + repr(e))
                    return False, None
                else:
                    # 然后再讲空数据同步至redis
                    redis_set_flag = True
                    redis_set_flag = modle_redis_apitestplanworktable.set_table(plan_id, new_blank_snap.table)
                    redis_set_flag = modle_redis_apitestplanworktable.set_time(plan_id)
                    if redis_set_flag:
                        return True, new_blank_snap.table
                    else:
                        return False, None
    # 如果有
    else:
        return True, cache_table_bytes.decode("utf8")


def set_snap_table_data(plan_id, table):
    # 从缓存中获取时间
    cache_time_bytes = modle_redis_apitestplanworktable.query_time(plan_id=plan_id)
    # 如果时间获取成功，则比较当前时间和缓存的时间
    if cache_time_bytes is not None:
        cache_time = datetime.datetime.strptime(cache_time_bytes.decode("utf8"), "%Y-%m-%d %H:%M:%S")
        # 如果没有超出15分钟（可配置），则仅刷新redis中内容
        if (datetime.datetime.now() - cache_time).seconds <= int(appconfig.get("task", "snapSyncInterval")):
            modle_redis_apitestplanworktable.set_table(plan_id, table)
            return True
        # 如果超出了15分钟（可配置），则先刷新redis中内容与时间，再同步至mysql生成快照，且更新时间
        else:
            redis_set_flag = True
            redis_set_flag = modle_redis_apitestplanworktable.set_table(plan_id, table)
            redis_set_flag = modle_redis_apitestplanworktable.set_time(plan_id)
            if redis_set_flag:
                # mysql中新增snap
                # 将status为1的snap全部置为失效
                try:
                    model_mysql_tablesnap.query.filter(
                        and_(
                            model_mysql_tablesnap.planId == plan_id,
                            model_mysql_tablesnap.status == 1
                        )
                    ).update({"status": 0})
                    mysqlpool.session.commit()
                except Exception as e:
                    api_logger.error("model_mysql_tablesnap数据更新失败，失败原因：" + repr(e))
                    return False
                else:
                    # 新增status为1的snap，内容即为接口传参内容
                    new_snap = model_mysql_tablesnap(
                        status=1,
                        planId=plan_id,
                        snapAddTime=datetime.datetime.now(),
                        table=table
                    )
                    try:
                        mysqlpool.session.add(new_snap)
                        mysqlpool.session.commit()
                    except Exception as e:
                        api_logger.error("new_snap数据写入失败，失败原因：" + repr(e))
                        return False
                    else:
                        return True
            else:
                return False
    # 如果时间获取失败，则直接将内容写入redis
    else:
        redis_set_flag = True
        redis_set_flag = modle_redis_apitestplanworktable.set_table(plan_id, table)
        redis_set_flag = modle_redis_apitestplanworktable.set_time(plan_id)
        return redis_set_flag


def create_snap_when_close(plan_id):
    redis_get_table_bytes = modle_redis_apitestplanworktable.query_table(plan_id)
    if redis_get_table_bytes is not None:
        # mysql中新增snap
        # 将status为1的snap全部置为失效
        try:
            model_mysql_tablesnap.query.filter(
                and_(
                    model_mysql_tablesnap.planId == plan_id,
                    model_mysql_tablesnap.status == 1
                )
            ).update({"status": 0})
            mysqlpool.session.commit()
        except Exception as e:
            api_logger.error("model_mysql_tablesnap数据更新失败，失败原因：" + repr(e))
            return False
        else:
            api_logger.debug("model_mysql_tablesnap数据更新成功")
            try:
                mysqlpool.session.add(model_mysql_tablesnap(
                    status=1,
                    planId=plan_id,
                    snapAddTime=datetime.datetime.now(),
                    table=redis_get_table_bytes.decode('utf-8')
                ))
                mysqlpool.session.commit()
            except Exception as e:
                api_logger.error("mysql_snaps数据写入失败，失败原因：" + repr(e))
            else:
                api_logger.debug("mysql_snaps数据写入成功")
            finally:
                # 不管如何，清空redis中的数据
                delete_flag = modle_redis_apitestplanworktable.delete(plan_id)
                api_logger.debug("redis中缓存清除完毕") if delete_flag else api_logger.debug("redis中缓存清除失败")
