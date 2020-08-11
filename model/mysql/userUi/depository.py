# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class depository(mysqlpool.Model):
    __tablename__ = "depository"
    # 定义column
    id = mysqlpool.Column(
        name="id",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    baseProjectId = mysqlpool.Column(
        name="baseProjectId",
        type_=INTEGER,
        nullable=False
    )
    userId = mysqlpool.Column(
        name="userId",
        type_=TINYINT(4),
        nullable=False
    )

    name = mysqlpool.Column(
        name="name",
        type_=VARCHAR(50),
        nullable=False
    )
    description = mysqlpool.Column(
        name="description",
        type_=VARCHAR(250),
        nullable=True
    )

    createTime = mysqlpool.Column(
        name="createTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
