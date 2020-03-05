# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, SMALLINT
from handler.pool import mysqlpool


class WorkerInfo(mysqlpool.Model):
    __tablename__ = "workerInfo"
    # 定义column
    workerId = mysqlpool.Column(
        name="workerId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    uniqueId = mysqlpool.Column(
        name="uniqueId",
        type_=VARCHAR(50),
        nullable=False
    )
    ip = mysqlpool.Column(
        name="ip",
        type_=VARCHAR(50),
        nullable=False
    )
    port = mysqlpool.Column(
        name="port",
        type_=SMALLINT,
        nullable=False
    )
    status = mysqlpool.Column(
        name="status",
        type_=TINYINT,
        nullable=False
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
