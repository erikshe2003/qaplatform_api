# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class Case(mysqlpool.Model):
    __tablename__ = "case"
    # 定义column
    id = mysqlpool.Column(
        name="id",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    title = mysqlpool.Column(
        name="title",
        type_=VARCHAR(200),
        nullable=False
    )
    depositoryId = mysqlpool.Column(
        name="depositoryId",
        type_=INTEGER,
        nullable=False
    )
    projectId = mysqlpool.Column(
        name="projectId",
        type_=INTEGER,
        nullable=True
    )
    columnId = mysqlpool.Column(
        name="columnId",
        type_=INTEGER,
        nullable=False
    )
    index = mysqlpool.Column(
        name="index",
        type_=INTEGER,
        nullable=False
    )
    columnLevel = mysqlpool.Column(
        name="columnLevel",
        type_=INTEGER,
        nullable=False
    )
    level = mysqlpool.Column(
        name="level",
        type_=TINYINT(2),
        nullable=False
    )
    type = mysqlpool.Column(
        name="type",
        type_=TINYINT(2),
        nullable=False
    )
    status = mysqlpool.Column(
        name="status",
        type_=TINYINT(2),
        nullable=False
    )
    userId = mysqlpool.Column(
        name="userId",
        type_=INTEGER,
        nullable=False
    )
    createTime = mysqlpool.Column(
        name="createTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    updateUserId = mysqlpool.Column(
        name="updateUserId",
        type_=INTEGER,
        nullable=True
    )
    updateTime = mysqlpool.Column(
        name="updateTime",
        type_=DATETIME,
        nullable=True,
        default=datetime.datetime.now
    )
    veri = mysqlpool.Column(
        name="veri",
        type_=TINYINT(4),
        nullable=True
    )
    arch = mysqlpool.Column(
        name="arch",
        type_=TINYINT(4),
        nullable=True
    )
    originalCaseId = mysqlpool.Column(
        name="originalCaseId",
        type_=INTEGER,
        nullable=False,
    )