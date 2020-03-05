# -*- coding: utf-8 -*-

import flask
import json
import route
import datetime
import time
import os
import zipfile

from sqlalchemy import and_, distinct, func

from handler.log import api_logger
from handler.pool import mysqlpool
from handler.socket.deploy import single_deploy, multi_deploy

from route.api.task import api_task
from route import plugin_map

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_planversion
from model.mysql import model_mysql_plancase
from model.mysql import model_mysql_planstep
from model.mysql import model_mysql_planplugin
from model.mysql import model_mysql_taskinfo
from model.mysql import model_mysql_userinfo
from model.redis import model_redis_userinfo

"""
    新增正式测试任务创建接口，此任务仅允许本人创建
    支持创建接口自动化测试以及接口性能测试任务
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            检查测试计划以及测试版本是否存在且该测试版本是否为临时版本
            新增调试任务
            将测试任务数据打包发送给执行应用
"""


@api_task.route('/newTestTask.json', methods=['post'])
@route.check_token
@route.check_user
@route.check_auth
@route.check_post_parameter(
    ['planId', int, 1, None],
    ['versionId', int, 1, None],
    ['description', str, None, 200],
    ['startType', int, 1, 2],
    ['runType', int, 1, 2]
)
def new_test_task():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {}
    }

    # 取出planId以及versionId
    mail_address = flask.request.headers['Mail']
    plan_id = flask.request.json['planId']
    version_id = flask.request.json['versionId']
    description = flask.request.json['description']
    start_type = flask.request.json['startType']
    run_type = flask.request.json['runType']
    # 如果startType为2则需要检查执行时间
    datetime_start_time = None
    datetime_end_time = None
    if start_type == 2:
        # 开始时间检查
        if 'startTime' not in flask.request.json:
            return route.error_msgs['msg_lack_keys']
        elif type(flask.request.json['startTime']) is not int:
            return route.error_msgs['msg_value_type_error']
        elif flask.request.json['startTime'] < int(time.time()):
            return route.error_msgs['msg_too_early']
        # 结束时间检查
        if 'endTime' not in flask.request.json:
            return route.error_msgs['msg_lack_keys']
        elif type(flask.request.json['endTime']) is not int:
            return route.error_msgs['msg_value_type_error']
        elif flask.request.json['endTime'] < flask.request.json['startTime'] + 10:
            return route.error_msgs['msg_task_time_error']
        try:
            datetime_start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(flask.request.json['startTime']))
            datetime_end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(flask.request.json['endTime']))
        except:
            return route.error_msgs['msg_data_error']
    # 如果runType为1则需要检查执行次数
    times = None
    if run_type == 1:
        if 'times' not in flask.request.json:
            return route.error_msgs['msg_lack_keys']
        elif type(flask.request.json['times']) is not int:
            return route.error_msgs['msg_value_type_error']
        elif flask.request.json['times'] < 1:
            return route.error_msgs['msg_data_error']
        times = flask.request.json['times']

    # 根据mail_address在缓存中查找账户id
    redis_user_info = model_redis_userinfo.query(user_email=mail_address)
    # 如果缓存中没查到，则查询mysql
    if redis_user_info is None:
        try:
            mysql_user_info = model_mysql_userinfo.query.filter(
                model_mysql_userinfo.userEmail == mail_address
            ).first()
            api_logger.debug(mail_address + "的账户基础信息读取成功")
        except Exception as e:
            api_logger.error(mail_address + "的账户基础信息读取失败，失败原因：" + repr(e))
            return route.error_msgs['msg_db_error']
        else:
            if mysql_user_info is None:
                return route.error_msgs['msg_no_user']
            else:
                user_id = mysql_user_info.userId
    else:
        # 格式化缓存中基础信息内容
        try:
            redis_user_info_json = json.loads(redis_user_info.decode("utf8"))
            api_logger.debug(mail_address + "的缓存账户数据json格式化成功")
        except Exception as e:
            api_logger.error(mail_address + "的缓存账户数据json格式化失败，失败原因：" + repr(e))
            return route.error_msgs['msg_json_format_fail']
        else:
            user_id = redis_user_info_json['userId']

    # 根据user_id/planId/versionId去mysql查询版本记录
    try:
        request_data = mysqlpool.session.query(
            model_mysql_planinfo.planType,
            model_mysql_planversion.isTemporary
        ).join(
            model_mysql_planversion,
            model_mysql_planinfo.planId == model_mysql_planversion.planId
        ).filter(
            and_(
                model_mysql_planinfo.planId == plan_id,
                model_mysql_planversion.versionId == version_id,
                model_mysql_planinfo.ownerId == user_id
            )
        ).first()
    except Exception as e:
        api_logger.debug(mail_address + "的临时测试计划版本读取失败，失败原因：" + repr(e))
        return route.error_msgs['msg_db_error']

    # 如果查询出来存在记录并且为正式版本，则继续，否则返回错误信息
    # 需排除数据异常
    if not request_data:
        return route.error_msgs['msg_no_data']
    elif request_data.isTemporary != 0:
        return route.error_msgs['msg_not_temporary']
    elif request_data.planType not in [1, 2]:
        return route.error_msgs['msg_no_plan_type']

    # 新增测试任务创建记录
    # 1.准备测试任务基础数据
    new_task_info = model_mysql_taskinfo(
        planId=plan_id,
        versionId=version_id,
        taskType=3,
        startType=start_type,
        endType=run_type,
        taskDescription=description,
        createTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        createUser=user_id
    )
    # 剩余未填写项目 startTime/endTime/excuteTimes/if_error/vUser/rampUpPeriod
    # startTime/endTime
    if start_type == 1:
        new_task_info.startTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elif start_type == 2:
        new_task_info.startTime = datetime_start_time
        new_task_info.endTime = datetime_end_time
    # excuteTimes
    if run_type == 1:
        new_task_info.excuteTimes = times
    # if_error
    # 暂时不支持自定义
    new_task_info.errorType = 1
    # rampUpPeriod
    # 暂时不支持自定义
    new_task_info.rampUpPeriod = 0
    # vUser
    # 根据planType判断是自动化测试任务还是性能测试任务
    if request_data.planType == 1:
        new_task_info.vUser = 1
    elif request_data.planType == 2:
        if 'UserNum' in flask.request.json:
            normal_v_user = flask.request.json['UserNum']
            if type(normal_v_user) is int and normal_v_user in range(1, 1001):
                new_task_info.vUser = normal_v_user
            else:
                return route.error_msgs['msg_value_type_error']
        else:
            return route.error_msgs['msg_lack_keys']
    try:
        mysqlpool.session.add(new_task_info)
        mysqlpool.session.commit()
    except Exception as e:
        api_logger.error("add new_task_info failed:" + repr(e))
        return route.error_msgs['msg_db_error']
    else:
        api_logger.debug("add new_task_info succeeded")

    # 准备待发送的测试任务文件
    # 根据临时版本的版本号，查询其下所有测试用例内容
    task_data = mysqlpool.session.query(
        model_mysql_plancase.caseId,
        model_mysql_planstep.stepId,
        model_mysql_planplugin.originalId,
        model_mysql_planplugin.sequence,
        model_mysql_planplugin.value
    ).outerjoin(
        model_mysql_planstep,
        model_mysql_plancase.caseId == model_mysql_planstep.caseId
    ).outerjoin(
        model_mysql_planplugin,
        model_mysql_planstep.stepId == model_mysql_planplugin.stepId
    ).filter(
        and_(
            model_mysql_plancase.versionId == version_id,
            model_mysql_plancase.status == 0,
            model_mysql_planstep.status == 0,
            model_mysql_planplugin.status == 0
        )
    ).order_by(
        model_mysql_plancase.sequence,
        model_mysql_planstep.sequence,
        model_mysql_planplugin.sequence
    ).all()
    # 格式化内容
    task_data_format = {
        "tid": new_task_info.taskId,
        "pid": plan_id,
        "steps": []
    }
    for td in task_data:
        # 如果sequence为0，则为self
        if td.sequence == 0:
            task_data_format['steps'].append({
                "cid": td.caseId,
                "sid": td.stepId,
                "self": {
                    "oid": td.originalId,
                    "v": td.value
                },
                "plugin": {
                    "pre": [],
                    "post": [],
                    "assert": []
                }
            })
        else:
            # 校验steps这个list的最后一个是否是待插入plugin的所属step
            if len(task_data_format['steps']) > 0 and task_data_format['steps'][-1]['sid'] == td.stepId:
                task_data_format['steps'][-1]['plugin'][plugin_map[td.originalId]].append({
                    "oid": td.originalId,
                    "v": td.value
                })
            elif len(task_data_format['steps']) == 0:
                api_logger.error("task_data格式化异常：待插入plugin但steps中无step")
            else:
                api_logger.error("task_data格式化异常：plugin数据异常")
    # 封装测试任务数据
    # 检查文件存放路径
    if not os.path.exists('file/'):
        api_logger.debug('main folder is not exist,try to create...')
        try:
            os.makedirs('file/')
        except Exception as e:
            api_logger.error('create main folder failed:' + repr(e))
            return route.error_msgs['msg_file_error']
        else:
            api_logger.debug('create main folder succeeded')
    the_now = datetime.datetime.now()
    the_year = str(the_now.year)
    the_month = str(the_now.month)
    the_day = str(the_now.day)
    if not os.path.exists('file/' + the_year):
        api_logger.debug('year folder is not exist,try to create...')
        try:
            os.makedirs('file/' + the_year)
        except Exception as e:
            api_logger.error('create year folder failed:' + repr(e))
            return route.error_msgs['msg_file_error']
        else:
            api_logger.debug('create year folder succeeded')
    if not os.path.exists('file/' + the_year + '/' + the_month):
        api_logger.debug('month folder is not exist,try to create...')
        try:
            os.makedirs('file/' + the_year + '/' + the_month)
        except Exception as e:
            api_logger.error('create month folder failed:' + repr(e))
            return route.error_msgs['msg_file_error']
        else:
            api_logger.debug('create month folder succeeded')
    if not os.path.exists('file/' + the_year + '/' + the_month + '/' + the_day):
        api_logger.debug('day folder is not exist,try to create...')
        try:
            os.makedirs('file/' + the_year + '/' + the_month + '/' + the_day)
        except Exception as e:
            api_logger.error('create day folder failed:' + repr(e))
            return route.error_msgs['msg_file_error']
        else:
            api_logger.debug('create day folder succeeded')
    dir_path = 'file/' + the_year + '/' + the_month + '/' + the_day
    task_dir_path = dir_path + '/task_%s_%s' % (
        str(new_task_info.taskId),
        the_now.strftime('%Y%m%d%H%M%S')
    )
    api_logger.debug('try to create task file folder...')
    try:
        os.makedirs(task_dir_path)
        os.makedirs(task_dir_path + '/file')
    except Exception as e:
        api_logger.error('create task folder failed:' + repr(e))
        return route.error_msgs['msg_file_error']
    else:
        api_logger.debug('create task folder succeeded')
        # 将测试任务数据存为json文件
        file = open(task_dir_path + '/task.json', 'w', encoding='utf-8')
        json.dump(task_data_format, file, ensure_ascii=False)
        file.close()
        # 将文件夹整个进行zip压缩
        z = zipfile.ZipFile(task_dir_path + '.zip', 'w', zipfile.ZIP_DEFLATED)
        # 将task.json/file添加入压缩包
        z.write(os.path.join(task_dir_path, 'task.json'), 'task.json')
        z.write(os.path.join(task_dir_path, 'file'), 'file')
        # 将file文件夹下所有文件添加入压缩包
        for dir_path, dir_names, file_names in os.walk(os.path.join(task_dir_path, 'file')):
            for fn in file_names:
                z.write(os.path.join(dir_path, fn), os.path.join('file', fn))
        z.close()

    # 根据计划类型
    if request_data.planType == 1:
        # 下发测试任务
        deploy_result = single_deploy(
            base=new_task_info,
            file=task_dir_path + '.zip'
        )
        if not deploy_result:
            return route.error_msgs['msg_deploy_failed']
    elif request_data.planType == 2:
        # 下发测试任务
        deploy_result = multi_deploy(
            base=new_task_info,
            file=task_dir_path + '.zip'
        )
        if not deploy_result:
            return route.error_msgs['msg_deploy_failed']

    return json.dumps(response_json)
