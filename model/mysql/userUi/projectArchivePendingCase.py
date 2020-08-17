# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class projectArchivePendingCase(mysqlpool.Model):
    __tablename__ = "projectArchivePendingCase"
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
    originalCaseId = mysqlpool.Column(
        name="originalCaseId",
        type_=TINYINT(4),
        nullable=False
    )
    projectIdCaseId = mysqlpool.Column(
        name="projectIdCaseId",
        type_=TINYINT(4),
        nullable=False
    )
    otherCaseId = mysqlpool.Column(
        name="otherCaseId",
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
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
