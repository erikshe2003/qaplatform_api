# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import INTEGER, TINYINT, DATETIME, VARCHAR, TEXT
from handler.pool import mysqlpool


class FunctionInfo(mysqlpool.Model):
    __tablename__ = "functionInfo"
    # 定义column
    functionId = mysqlpool.Column(
        name="functionId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    functionName = mysqlpool.Column(
        name="functionName",
        type_=VARCHAR(100),
        nullable=False
    )
    functionAlias = mysqlpool.Column(
        name="functionAlias",
        type_=VARCHAR(100),
        nullable=False
    )
    functionDescription = mysqlpool.Column(
        name="functionDescription",
        type_=TEXT,
        nullable=True
    )
    functionType = mysqlpool.Column(
        name="functionType",
        type_=TINYINT(1),
        nullable=False
    )
    rootId = mysqlpool.Column(
        name="rootId",
        type_=INTEGER,
        nullable=False
    )
    parentId = mysqlpool.Column(
        name="parentId",
        type_=INTEGER,
        nullable=False
    )
    hasNode = mysqlpool.Column(
        name="hasNode",
        type_=TINYINT(1),
        nullable=False
    )
    functionAddTime = mysqlpool.Column(
        name="functionAddTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
