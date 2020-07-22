# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class projectMember(mysqlpool.Model):
    __tablename__ = "projectMember"
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
    userId = mysqlpool.Column(
        name="userId",
        type_=INTEGER,
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
