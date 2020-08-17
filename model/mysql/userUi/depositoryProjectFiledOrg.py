# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class depositoryProjectFiledOrg(mysqlpool.Model):
    __tablename__ = "depositoryProjectFiledOrg"
    # 定义column
    id = mysqlpool.Column(
        name="id",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    projectId = mysqlpool.Column(
        name="projectId",
        type_=INTEGER,
        nullable=False
    )
    depositoryId = mysqlpool.Column(
        name="depositoryId",
        type_=TINYINT(4),
        nullable=False
    )
    result = mysqlpool.Column(
        name="result",
        type_=TINYINT(4),
        nullable=False
    )
    createTime = mysqlpool.Column(
        name="createTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    startTime = mysqlpool.Column(
        name="startTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )

    finishTime = mysqlpool.Column(
        name="finishTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
