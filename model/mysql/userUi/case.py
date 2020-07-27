# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class case(mysqlpool.Model):
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
        type_=TINYINT(4),
        nullable=True
    )
    projectId = mysqlpool.Column(
        name="projectId",
        type_=TINYINT(4),
        nullable=True
    )
    columnId = mysqlpool.Column(
        name="columnId",
        type_=TINYINT(4),
        nullable=True
    )

    index = mysqlpool.Column(
        name="index",
        type_=VARCHAR(200),
        nullable=True
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
        type_=TINYINT(4),
        nullable=True
    )
    createTime = mysqlpool.Column(
        name="createTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    updateUserId = mysqlpool.Column(
        name="updateUserId",
        type_=TINYINT(4),
        nullable=True
    )
    updateTime = mysqlpool.Column(
        name="updateTime",
        type_=DATETIME,
        nullable=False,
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