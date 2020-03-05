# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME
from handler.pool import mysqlpool


class TaskAssign(mysqlpool.Model):
    __tablename__ = "taskAssign"
    # 定义column
    assignId = mysqlpool.Column(
        name="assignId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    taskId = mysqlpool.Column(
        name="taskId",
        type_=INTEGER,
        nullable=False
    )
    workerId = mysqlpool.Column(
        name="workerId",
        type_=INTEGER,
        nullable=False
    )
    vuser = mysqlpool.Column(
        name="vuser",
        type_=INTEGER,
        nullable=False
    )
    status = mysqlpool.Column(
        name="status",
        type_=TINYINT,
        nullable=False
    )
    startTime = mysqlpool.Column(
        name="startTime",
        type_=DATETIME,
        nullable=True
    )
    finishTime = mysqlpool.Column(
        name="finishTime",
        type_=DATETIME,
        nullable=True
    )
    createTime = mysqlpool.Column(
        name="createTime",
        type_=DATETIME,
        nullable=False
    )
    updateTime = mysqlpool.Column(
        name="updateTime",
        type_=DATETIME,
        nullable=True
    )
