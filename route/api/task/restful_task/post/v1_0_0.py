# -*- coding: utf-8 -*-

import flask
import json
import route
import shutil
import datetime
import time
import os
import zipfile

from sqlalchemy import and_

from handler.log import api_logger
from handler.config import appconfig
from handler.pool import mysqlpool
from handler.socket.deploy import single_deploy

from model.mysql import model_mysql_planinfo
from model.mysql import model_mysql_tablesnap
from model.mysql import model_mysql_taskinfo
from model.mysql import model_mysql_userinfo
from model.redis import model_redis_userinfo
from model.redis import modle_redis_apitestplanworktable

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


@route.check_token
@route.check_user
@route.check_auth
@route.check_post_parameter(
    ['planId', int, 1, None],
    ['description', str, None, 200],
    ['startType', int, 1, 2],
    ['runType', int, 1, 2]
)
def task_post():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {}
    }

    # 取出数据
    # header
    mail_address = flask.request.headers['Mail']
    # body
    plan_id = flask.request.json['planId']
    description = flask.request.json['description']
    start_type = flask.request.json['startType']
    run_type = flask.request.json['runType']

    # 如果startType为2则需要检查执行时间
    datetime_start_time = None
    datetime_end_time = None
    if start_type == 2:
        # 开始时间检查
        if 'startTime' not in flask.request.json:
            api_logger.debug("传参缺少startTime")
            return route.error_msgs[302]['msg_request_params_incomplete']
        elif type(flask.request.json['startTime']) is not int:
            api_logger.debug("传参startTime类型错误")
            return route.error_msgs[301]['msg_value_type_error']
        elif flask.request.json['startTime'] < int(time.time()):
            api_logger.debug("传参startTime大小错误")
            return route.error_msgs[201]['msg_too_early']
        # 结束时间检查
        if 'endTime' not in flask.request.json:
            api_logger.debug("传参缺少endTime")
            return route.error_msgs[302]['msg_request_params_incomplete']
        elif type(flask.request.json['endTime']) is not int:
            api_logger.debug("传参endTime类型错误")
            return route.error_msgs[301]['msg_value_type_error']
        elif flask.request.json['endTime'] < flask.request.json['startTime'] + 10:
            api_logger.debug("传参endTime大小错误")
            return route.error_msgs[201]['msg_task_time_error']
        try:
            datetime_start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(flask.request.json['startTime']))
            datetime_end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(flask.request.json['endTime']))
        except:
            return route.error_msgs[201]['msg_data_error']
    # 如果runType为1则需要检查执行次数
    times = None
    if run_type == 1:
        if 'times' not in flask.request.json:
            return route.error_msgs[302]['msg_request_params_incomplete']
        elif type(flask.request.json['times']) is not int:
            return route.error_msgs[301]['msg_value_type_error']
        elif flask.request.json['times'] < 1:
            return route.error_msgs[201]['msg_data_error']
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
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_user_info is None:
                return route.error_msgs[201]['msg_no_user']
            else:
                user_id = mysql_user_info.userId
    else:
        # 格式化缓存中基础信息内容
        try:
            redis_user_info_json = json.loads(redis_user_info.decode("utf8"))
            api_logger.debug(mail_address + "的缓存账户数据json格式化成功")
        except Exception as e:
            api_logger.error(mail_address + "的缓存账户数据json格式化失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_json_format_fail']
        else:
            user_id = redis_user_info_json['userId']

    # 为了将来能够看日志，必须要有不变的快照数据，所以tableSnap的不靠谱
    # 尝试于redis读取工作台快照临时数据
    # 如果有，以这些内容发起测试任务
    # 如果无，则读取mysql中最新的内容，发起测试任务
    tablesnap_data = None
    redis_get_table_bytes = modle_redis_apitestplanworktable.query_table(plan_id)
    if redis_get_table_bytes is not None:
        tablesnap_data = redis_get_table_bytes.decode('utf-8')
    else:
        # 根据planId去查询工作台快照内容
        try:
            mysql_tablesnap = model_mysql_tablesnap.query.filter(
                and_(
                    model_mysql_tablesnap.planId == plan_id,
                    model_mysql_tablesnap.status == 1
                )
            ).first()
            api_logger.debug("接口测试计划工作台快照内容查找成功")
        except Exception as e:
            api_logger.debug("接口测试计划工作台快照内容查找失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            # 如果查询出来存在记录并且为正式版本，则继续，否则返回错误信息
            # 需排除数据异常
            if not mysql_tablesnap:
                return route.error_msgs[201]['msg_no_data']
            else:
                tablesnap_data = mysql_tablesnap.table

    # 新增测试任务创建记录
    # 1.准备测试任务基础数据
    new_task_info = model_mysql_taskinfo(
        planId=plan_id,
        snap=tablesnap_data,
        taskType=1,
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
    if 'userNum' in flask.request.json:
        normal_v_user = flask.request.json['userNum']
        if type(normal_v_user) is int and normal_v_user in range(1, 1001):
            new_task_info.vUser = normal_v_user
        else:
            return route.error_msgs[301]['msg_value_type_error']
    else:
        return route.error_msgs[302]['msg_request_params_incomplete']
    # 新增测试任务记录
    try:
        mysqlpool.session.add(new_task_info)
        mysqlpool.session.commit()
    except Exception as e:
        api_logger.error("新增测试任务失败，原因:" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        api_logger.debug("新增测试任务成功")

    # 准备待发送的测试任务文件
    # 将工作台内容保存为task.json文件
    # 封装测试任务数据
    # 检查文件存放路径
    if not os.path.exists('file/'):
        api_logger.debug('存放测试任务文件的file主目录不存在，尝试创建...')
        try:
            os.makedirs('file/')
        except Exception as e:
            api_logger.error('存放测试任务文件的file目录创建失败，原因:' + repr(e))
            return route.error_msgs[500]['msg_file_error']
        else:
            api_logger.debug('存放测试任务文件的file目录创建成功')
    the_now = datetime.datetime.now()
    the_year = str(the_now.year)
    the_month = str(the_now.month)
    the_day = str(the_now.day)
    if not os.path.exists('file/' + the_year):
        api_logger.debug('年份目录不存在，尝试创建...')
        try:
            os.makedirs('file/' + the_year)
        except Exception as e:
            api_logger.error('年份目录创建失败，原因:' + repr(e))
            return route.error_msgs[500]['msg_file_error']
        else:
            api_logger.debug('年份目录创建成功')
    if not os.path.exists('file/' + the_year + '/' + the_month):
        api_logger.debug('月份目录不存在，尝试创建...')
        try:
            os.makedirs('file/' + the_year + '/' + the_month)
        except Exception as e:
            api_logger.error('月份目录创建失败，原因:' + repr(e))
            return route.error_msgs[500]['msg_file_error']
        else:
            api_logger.debug('月份目录创建成功')
    if not os.path.exists('file/' + the_year + '/' + the_month + '/' + the_day):
        api_logger.debug('日子目录不存在，尝试创建...')
        try:
            os.makedirs('file/' + the_year + '/' + the_month + '/' + the_day)
        except Exception as e:
            api_logger.error('日子目录创建失败，原因:' + repr(e))
            return route.error_msgs[500]['msg_file_error']
        else:
            api_logger.debug('日子目录创建成功')
    dir_path = 'file/' + the_year + '/' + the_month + '/' + the_day
    task_dir_path = dir_path + '/task_%s_%s' % (
        str(new_task_info.taskId),
        the_now.strftime('%Y%m%d%H%M%S')
    )
    api_logger.debug('尝试创建测试任务目标目录...')
    try:
        # 于file目录下创建 年/月/日/task_taskId_时间戳 文件夹
        os.makedirs(task_dir_path)
        # 将项目文件夹（其中为参数化文件）复制到task文件夹下
        resource_path = appconfig.get("task", "filePutDir")
        resource_path = resource_path[:-1] if resource_path[-1] == "/" else resource_path
        resource_path = "%s/%s" % (resource_path, plan_id)
        # 根据配置文件中的路径，判断测试计划文件夹是否存在
        if os.path.exists(resource_path) is False or os.path.isdir(resource_path) is False:
            os.makedirs(task_dir_path + '/files')
        else:
            shutil.copytree(resource_path, task_dir_path + '/files')
    except Exception as e:
        api_logger.error('测试任务目标目录创建失败，原因:' + repr(e))
        return route.error_msgs[500]['msg_file_error']
    else:
        api_logger.debug('测试任务目标目录创建成功')
        # 将测试任务数据存为json文件
        file = open(task_dir_path + '/task.json', 'w', encoding='utf-8')
        file.write(tablesnap_data)
        file.close()
        # 将文件夹整个进行zip压缩
        z = zipfile.ZipFile(task_dir_path + '.zip', 'w', zipfile.ZIP_DEFLATED)
        # 将task.json/file添加入压缩包
        z.write(os.path.join(task_dir_path, 'task.json'), 'task.json')
        z.write(os.path.join(task_dir_path, 'files'), 'files')
        # 将file文件夹下所有文件添加入压缩包
        for dir_path, dir_names, file_names in os.walk(os.path.join(task_dir_path, 'files')):
            for fn in file_names:
                if fn not in z.NameToInfo:
                    z.write(os.path.join(dir_path, fn), os.path.join('files', fn))
        z.close()

    # 查询计划类型
    try:
        mysql_planinfo = model_mysql_planinfo.query.filter(
            model_mysql_planinfo.planId == plan_id
        ).first()
    except Exception as e:
        api_logger.debug("model_mysql_planinfo数据读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        # 根据计划类型下发测试任务
        if mysql_planinfo.planType == 1:
            deploy_result, deploy_msg = single_deploy(
                base=new_task_info,
                file=task_dir_path + '.zip'
            )
            if not deploy_result:
                response_json['error_code'] = 500
                response_json['error_msg'] = '测试任务下发失败，原因:%s，请联系管理员或稍后再发起测试任务' % deploy_msg
                return json.dumps(response_json)

    return response_json
