# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import INTEGER, TINYINT, DATETIME
from handler.pool import mysqlpool


class FunctionOrg(mysqlpool.Model):
    __tablename__ = "functionOrg"
    # 定义column
    orgId = mysqlpool.Column(
        name="orgId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    functionId = mysqlpool.Column(
        name="functionId",
        type_=INTEGER,
        nullable=False
    )
    apiId = mysqlpool.Column(
        name="apiId",
        type_=INTEGER,
        nullable=False
    )
    orgStatus = mysqlpool.Column(
        name="orgStatus",
        type_=TINYINT(1),
        nullable=False
    )
    orgAddTime = mysqlpool.Column(
        name="orgAddTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    orgUpdateTime = mysqlpool.Column(
        name="orgUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
