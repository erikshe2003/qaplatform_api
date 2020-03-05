# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, MEDIUMTEXT
from handler.pool import mysqlpool


class TaskInfo(mysqlpool.Model):
    __tablename__ = "taskInfo"
    # 定义column
    taskId = mysqlpool.Column(
        name="taskId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    planId = mysqlpool.Column(
        name="planId",
        type_=INTEGER,
        nullable=False
    )
    snap = mysqlpool.Column(
        name="snap",
        type_=MEDIUMTEXT,
        nullable=False
    )
    taskType = mysqlpool.Column(
        name="taskType",
        type_=TINYINT,
        nullable=False
    )
    taskDescription = mysqlpool.Column(
        name="taskDescription",
        type_=VARCHAR(200),
        nullable=True
    )
    startTime = mysqlpool.Column(
        name="startTime",
        type_=DATETIME,
        nullable=True
    )
    endTime = mysqlpool.Column(
        name="endTime",
        type_=DATETIME,
        nullable=True
    )
    startType = mysqlpool.Column(
        name="startType",
        type_=TINYINT,
        nullable=False
    )
    endType = mysqlpool.Column(
        name="endType",
        type_=TINYINT,
        nullable=False
    )
    excuteTimes = mysqlpool.Column(
        name="excuteTimes",
        type_=INTEGER,
        nullable=True
    )
    errorType = mysqlpool.Column(
        name="errorType",
        type_=TINYINT,
        nullable=False
    )
    createTime = mysqlpool.Column(
        name="createTime",
        type_=DATETIME,
        nullable=False
    )
    createUser = mysqlpool.Column(
        name="createUser",
        type_=INTEGER,
        nullable=False
    )
    vUser = mysqlpool.Column(
        name="vUser",
        type_=INTEGER,
        nullable=False
    )
    rampUpPeriod = mysqlpool.Column(
        name="rampUpPeriod",
        type_=INTEGER,
        nullable=False
    )