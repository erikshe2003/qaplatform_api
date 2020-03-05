# -*- coding: utf-8 -*-


import socket
import datetime
import struct

from handler.pool import mysqlpool
from handler.log import sys_logger, db_logger
from handler.socket import dataFormat

from multiprocessing.dummy import Pool as ThreadPool

from model.mysql import model_mysql_workerinfo
from model.mysql import model_mysql_taskassign


def update_finishtime(assign_id):
    try:
        assign_data = model_mysql_taskassign.query.filter(
            model_mysql_taskassign.assignId == assign_id
        ).first()
        if assign_data:
            assign_data.finishTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mysqlpool.session.commit()
    except Exception as e:
        db_logger.error("assign_id:" + str(assign_id) + " 信息更新失败，失败原因:" + repr(e))
    else:
        db_logger.debug("assign_id:" + str(assign_id) + " 信息更新成功")


def kill(assign_data):
    assign_id, task_id, worker_id, worker_ip, worker_port = assign_data
    # 打包action
    struct_action_data = struct.pack(dataFormat['action'], 'stopTestTask'.encode())
    # 初始化并发送第一个请求
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sys_logger.debug(str(worker_id) + '|prepare to send action...')
    try:
        s.connect((worker_ip, worker_port))
        s.send(struct_action_data)
    except Exception as e:
        sys_logger.error(str(worker_id) + '|send action failed:' + repr(e))
    else:
        sys_logger.debug(str(worker_id) + '|send action succeeded')
        sys_logger.debug(str(worker_id) + '|listen action response from worker...')
        worker_response = s.recv(1024)
        sys_logger.debug(str(worker_id) + '|get action response from worker')
        worker_response = worker_response.decode()
        if worker_response == 'Success':
            # 打包base_data
            struct_base_data = struct.pack(
                dataFormat['stopTestTask'],
                task_id
            )
            sys_logger.debug(str(worker_id) + '|prepare to send base data...')
            try:
                s.send(struct_base_data)
            except Exception as e:
                sys_logger.error(str(worker_id) + '|send base data failed:' + repr(e))
            else:
                sys_logger.debug(str(worker_id) + '|send base data succeeded')
                sys_logger.debug(str(worker_id) + '|listen base response from worker...')
                worker_response = s.recv(1024)
                sys_logger.debug(str(worker_id) + '|get base response from worker')
                if worker_response.decode() == 'Success':
                    pass


def kill_task(assign_data):
    """
        :param assign_data: 测试任务下发数据
        :return: 无返回
    """
    # 获取已下发测试任务的所有有效的worker信息
    good_workers = []
    # 轮询assign_data中的worker，判断是否可用
    for ad in assign_data:
        # 根据ad的workerId查询workerInfo
        try:
            worker_info = model_mysql_workerinfo.query.filter(
                model_mysql_workerinfo.workerId == ad.workerId
            ).first()
        except Exception as e:
            db_logger.error("worker:" + str(ad.workerId) + " 信息查询失败，失败原因:" + repr(e))
        else:
            db_logger.debug("worker:" + str(ad.workerId) + " 信息查询成功")
            # 判断数据是否存在
            if worker_info is None:
                # 如果worker的条目没有了，则将对应下发记录的finishTime直接赋上
                update_finishtime(ad.assignId)
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                r = s.connect_ex((worker_info.ip, worker_info.port))
                if r != 0:
                    # 将worker的状态置为异常
                    worker_info.status = 0
                    # 如果worker的状态为异常，则将对应下发记录的finishTime直接赋上
                    update_finishtime(ad.assignId)
                else:
                    # 将worker的状态置为正常
                    worker_info.status = 1
                    good_workers.append(ad)
                try:
                    mysqlpool.session.commit()
                except Exception as e:
                    sys_logger.error("worker:" + str(ad.workerId) + " 信息更新失败，失败原因:" + repr(e))
                else:
                    sys_logger.debug("worker:" + str(ad.workerId) + " 信息更新成功")
                s.close()

    # 如果缺少可用worker
    if len(good_workers) < 1:
        pass
    else:
        # 开启线程池
        pool = ThreadPool(len(good_workers))
        pool.map(kill, good_workers)
        pool.close()
        pool.join()
