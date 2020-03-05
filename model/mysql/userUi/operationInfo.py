# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TEXT, DATETIME
from handler.pool import mysqlpool


class OperationInfo(mysqlpool.Model):
    __tablename__ = "operationInfo"
    # 定义column
    operationId = mysqlpool.Column(
        name="operationId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    operationAlias = mysqlpool.Column(
        name="operationAlias",
        type_=VARCHAR(100),
        nullable=False
    )
    operationDescription = mysqlpool.Column(
        name="operationDescription",
        type_=TEXT,
        nullable=True
    )
    operationAddTime = mysqlpool.Column(
        name="operationAddTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
