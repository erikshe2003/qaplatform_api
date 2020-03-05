# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME
from handler.pool import mysqlpool


class UserOperationRecord(mysqlpool.Model):
    __tablename__ = "userOperationRecord"
    # 定义column
    recordId = mysqlpool.Column(
        name="recordId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    userId = mysqlpool.Column(
        name="userId",
        type_=INTEGER,
        nullable=False
    )
    operationId = mysqlpool.Column(
        name="operationId",
        type_=INTEGER,
        nullable=False
    )
    recordCode = mysqlpool.Column(
        name="recordCode",
        type_=VARCHAR(200),
        nullable=False
    )
    recordStatus = mysqlpool.Column(
        name="recordStatus",
        type_=TINYINT(1),
        nullable=False
    )
    recordValidTime = mysqlpool.Column(
        name="recordValidTime",
        type_=DATETIME,
        nullable=False
    )
    recordAddTime = mysqlpool.Column(
        name="recordAddTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    recordUpdateTime = mysqlpool.Column(
        name="recordUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
