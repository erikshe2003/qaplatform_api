# -*- coding: utf-8 -*-


import socket
import struct
import os
import random
import datetime

from handler.pool import mysqlpool
from handler.log import sys_logger
from handler.socket import dataFormat

from multiprocessing.dummy import Pool as ThreadPool

from model.mysql import model_mysql_workerinfo
from model.mysql import model_mysql_taskassign


def deploy(worker_base_file):
    the_worker, base, file = worker_base_file
    the_worker_id = the_worker.workerId
    msg = ''
    the_date = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # 新增下发测试任务记录
    new_task_assign = model_mysql_taskassign(
        taskId=base.taskId,
        workerId=the_worker_id,
        vuser=base.vUser,
        status=0,
        createTime=the_date,
        updateTime=the_date
    )
    try:
        # 下发记录入库
        mysqlpool.session.add(new_task_assign)
        mysqlpool.session.commit()
    except Exception as e:
        msg = "测试任务下发记录新增失败，失败原因:" + repr(e)
        sys_logger.debug(msg)
        return False, msg
    else:
        sys_logger.debug("测试任务下发记录新增成功")
        # 打包action
        # 初始化并发送第一个请求
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sys_logger.debug('workerId:%d,准备发送action...' % the_worker_id)
        try:
            s.connect((the_worker.ip, the_worker.port))
            s.send(struct.pack(dataFormat['action'], 'newTestTask'.encode()))
        except Exception as e:
            msg = 'workerId:%d,发送action失败:%s' % (the_worker_id, repr(e))
            sys_logger.error(msg)
            return False, msg
        else:
            msg = 'workerId:%d,发送action成功' % the_worker_id
            sys_logger.debug(msg)
            msg = 'workerId:%d,准备接收action返回...' % the_worker_id
            sys_logger.debug(msg)
            worker_response = s.recv(1024)
            msg = 'workerId:%d,接收到action返回' % the_worker_id
            sys_logger.debug(msg)
            worker_response = worker_response.decode()
            if worker_response == 'Success':
                msg = 'workerId:%d,准备发送basedata...' % the_worker_id
                sys_logger.debug(msg)
                try:
                    # 打包并发送base_data
                    s.send(struct.pack(
                        dataFormat['newTestTask'],
                        base.taskId,
                        base.vUser,
                        base.rampUpPeriod,
                        base.startType,
                        base.endType,
                        base.errorType,
                        base.excuteTimes if base.excuteTimes else 0,
                        os.stat(file).st_size,
                        str(base.startTime).encode() if base.startTime else ''.encode(),
                        str(base.endTime).encode() if base.endTime else ''.encode()
                    ))
                except Exception as e:
                    msg = 'workerId:%d,发送basedata失败:%s' % (the_worker_id, repr(e))
                    sys_logger.error(msg)
                    return False, msg
                else:
                    msg = 'workerId:%d,发送basedata成功' % the_worker_id
                    sys_logger.debug(msg)
                    msg = 'workerId:%d,准备接收basedata返回...' % the_worker_id
                    sys_logger.debug(msg)
                    worker_response = s.recv(1024)
                    msg = 'workerId:%d,接收到basedata返回' % the_worker_id
                    sys_logger.debug(msg)
                    worker_response = worker_response.decode()
                    if worker_response == 'Success':
                        task_file = open(file, 'rb')
                        msg = 'workerId:%d,准备发送测试任务数据及文件的压缩包...' % the_worker_id
                        sys_logger.debug(msg)
                        try:
                            while True:
                                file_data = task_file.read(1024)
                                if not file_data:
                                    break
                                s.send(file_data)
                        except Exception as e:
                            msg = 'workerId:%d,发送压缩包失败:%s' % (the_worker_id, repr(e))
                            sys_logger.error(msg)
                            return False, msg
                        else:
                            task_file.close()
                            msg = 'workerId:%d,发送压缩包成功' % the_worker_id
                            sys_logger.debug(msg)
                            msg = 'workerId:%d,准备接收压缩包返回...' % the_worker_id
                            sys_logger.debug(msg)
                            worker_response = s.recv(1024)
                            msg = 'workerId:%d,接收到压缩包返回' % the_worker_id
                            sys_logger.debug(msg)
                            worker_response = worker_response.decode()
                            if worker_response == 'Success':
                                # 下发结果入库
                                new_task_assign.status = 1
                                new_task_assign.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                msg = 'workerId:%d,压缩包处理成功' % the_worker_id
                                sys_logger.debug(msg)
                                try:
                                    mysqlpool.session.commit()
                                except Exception as e:
                                    msg = '测试任务下发记录更新失败，失败原因:%s' % repr(e)
                                    sys_logger.debug(msg)
                                    return False, msg
                                else:
                                    msg = '测试任务下发记录更新成功'
                                    sys_logger.debug(msg)
                                    return True, '测试任务下发成功'
                            else:
                                # 下发结果入库
                                new_task_assign.status = -1
                                new_task_assign.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                msg = 'workerId:%d,压缩包处理失败:%s' % (
                                    the_worker_id,
                                    worker_response.split('.')[1] if len(worker_response.split('.')) > 1 else '原因未知'
                                )
                                sys_logger.error(msg)
                                try:
                                    mysqlpool.session.commit()
                                except Exception as e:
                                    msg = '测试任务下发记录更新失败，失败原因:%s' % repr(e)
                                    sys_logger.debug(msg)
                                    return False, msg
                                else:
                                    msg = '测试任务下发记录更新成功'
                                    sys_logger.debug(msg)
                                    return False, 'workerId:%d,压缩包处理失败:%s' % (
                                        the_worker_id,
                                        worker_response.split('.')[1] if len(
                                            worker_response.split('.')) > 1 else '原因未知'
                                    )
                    else:
                        # 下发结果入库
                        new_task_assign.status = -1
                        new_task_assign.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        msg = 'workerId:%d,basedata处理失败:%s' % (
                            the_worker_id,
                            worker_response.split('.')[1] if len(worker_response.split('.')) > 1 else '原因未知'
                        )
                        sys_logger.error(msg)
                        try:
                            mysqlpool.session.commit()
                        except Exception as e:
                            msg = '测试任务下发记录更新失败，失败原因:%s' % repr(e)
                            sys_logger.debug(msg)
                            return False, msg
                        else:
                            msg = '测试任务下发记录更新成功'
                            sys_logger.debug(msg)
                            return False, 'workerId:%d,basedata处理失败:%s' % (
                                the_worker_id,
                                worker_response.split('.')[1] if len(
                                    worker_response.split('.')) > 1 else '原因未知'
                            )
            else:
                # 下发结果入库
                new_task_assign.status = -1
                new_task_assign.updateTime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                msg = 'workerId:%d,action处理失败:%s' % (
                    the_worker_id,
                    worker_response.split('.')[1] if len(worker_response.split('.')) > 1 else '原因未知'
                )
                sys_logger.error(msg)
                try:
                    mysqlpool.session.commit()
                except Exception as e:
                    msg = '测试任务下发记录更新失败，失败原因:%s' % repr(e)
                    sys_logger.debug(msg)
                    return False, msg
                else:
                    msg = '测试任务下发记录更新成功'
                    sys_logger.debug(msg)
                    return False, 'workerId:%d,action处理失败:%s' % (
                        the_worker_id,
                        worker_response.split('.')[1] if len(
                            worker_response.split('.')) > 1 else '原因未知'
                    )


def single_deploy(base, file):
    """
        :param base: 接收测试任务基础信息
        :param file: 接收测试任务文件
        :return: True/False
    """
    # 获取当前所有有效的worker信息
    try:
        all_workers = model_mysql_workerinfo.query.filter(
            model_mysql_workerinfo.status == 1
        ).all()
    except Exception as e:
        msg = "获取执行应用列表失败，失败原因：" + repr(e)
        sys_logger.debug(msg)
        return False, msg

    # 检查worker
    good_workers = []
    if not all_workers:
        msg = "当前系统无可用worker"
        sys_logger.warn(msg)
        return False, msg
    else:
        # 轮询可用worker，判断是否确实可用
        for aw in all_workers:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            r = s.connect_ex((aw.ip, aw.port))
            if r != 0:
                # 将worker的状态置为异常
                aw.status = 0
                try:
                    mysqlpool.session.commit()
                except Exception as e:
                    sys_logger.error("worker:" + str(aw.workerId) + " 信息更新失败，失败原因:" + repr(e))
                else:
                    sys_logger.debug("worker:" + str(aw.workerId) + " 信息更新成功")
            else:
                good_workers.append(aw)
            s.close()

    # 如果缺少可用worker，则报错
    if len(good_workers) < 1:
        msg = "当前系统无可用worker"
        sys_logger.error(msg)
        return False, msg
    else:
        # 从可用worker列表中任取一个进行下发操作
        # 如果失败，则把错误返回累计起来以便写warn日志，并继续尝试，直到下发成功
        deploy_msg = ''
        deploy_result = False
        while len(good_workers) > 0 and not deploy_result:
            i = random.randint(0, len(good_workers) - 1)
            # 调用deploy
            deploy_result, msg = deploy([good_workers[i], base, file])
            deploy_msg += msg + ';'
            good_workers.pop(i)
        if deploy_result:
            sys_logger.debug(deploy_msg)
        else:
            sys_logger.warn(deploy_msg)

        return deploy_result, deploy_msg


def multi_deploy(base, file):
    """
        :param base: 接收测试任务基础信息
        :param file: 接收测试任务文件
        :return: True/False
    """
    # 获取当前所有有效的worker信息
    try:
        all_workers = model_mysql_workerinfo.query.filter(
            model_mysql_workerinfo.status == 1
        ).all()
    except Exception as e:
        sys_logger.debug("获取执行应用列表失败，失败原因：" + repr(e))
        return False

    # 检查worker
    good_workers = []
    if not all_workers:
        sys_logger.debug("当前系统无可用worker")
        return False
    else:
        # 轮询可用worker，判断是否确实可用
        for aw in all_workers:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            r = s.connect_ex((aw.ip, aw.port))
            if r != 0:
                # 将worker的状态置为异常
                aw.status = 0
                try:
                    mysqlpool.session.commit()
                except Exception as e:
                    sys_logger.error("worker:" + str(aw.workerId) + " 信息更新失败，失败原因:" + repr(e))
                else:
                    sys_logger.debug("worker:" + str(aw.workerId) + " 信息更新成功")
            else:
                good_workers.append(aw)
                s.send(struct.pack(dataFormat['action'], 'test'.encode()))
            s.close()

    # 如果缺少可用worker，则报错
    if len(good_workers) < 1:
        sys_logger.error("当前系统无可用worker")
        return False

    # 根据worker数量拆分base中的vUser
    if len(good_workers) >= base.vUser:
        sys_logger.debug("虚拟用户数量较少，仅选择单机运行")
        # 如果vUser数量小于等于worker数量，则随机取一个worker
        the_worker = random.sample(good_workers, 1)[0]
        # 调用deploy
        deploy_result = deploy([the_worker, base, file])
        return deploy_result
    # 如果vUser数量大于worker数量，则均分
    else:
        sys_logger.debug("虚拟用户数量较多，选择多机运行")
        u1 = base.vUser // len(good_workers)
        # 判断能否整除
        if base.vUser % len(good_workers) == 0:
            users = [u1] * len(good_workers)
        else:
            users = [u1] * (len(good_workers) - 1)
            users.append(base.vUser - u1 * (len(good_workers) - 1))
        # 开启线程池
        pool = ThreadPool(len(good_workers))
        worker_base_list = []
        i = 0
        for gw in good_workers:
            base.vUser = users[i]
            worker_base_list.append([gw, base, file])
            i += 1
        pool.map(deploy, worker_base_list)
        pool.close()
        pool.join()
        return True
