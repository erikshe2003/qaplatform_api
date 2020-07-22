# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class project(mysqlpool.Model):
    __tablename__ = "project"
    # 定义column
    id = mysqlpool.Column(
        name="id",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    name = mysqlpool.Column(
        name="name",
        type_=VARCHAR(50),
        nullable=False
    )
    description = mysqlpool.Column(
        name="description",
        type_=VARCHAR(200),
        nullable=True
    )
    coverOssPath = mysqlpool.Column(
        name="coverOssPath",
        type_=TEXT(1000),
        nullable=True
    )
    userId = mysqlpool.Column(
        name="userId",
        type_=TINYINT(4),
        nullable=False
    )
    depositoryId = mysqlpool.Column(
        name="depositoryId",
        type_=TINYINT(4),
        nullable=False
    )
    originalProjectId = mysqlpool.Column(
        name="originalProjectId",
        type_=TINYINT(4),
        nullable=False
    )
    status = mysqlpool.Column(
        name="status",
        type_=TINYINT(4),
        nullable=False
    )
    createTime = mysqlpool.Column(
        name="createTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )

    updateTime = mysqlpool.Column(
        name="updateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
