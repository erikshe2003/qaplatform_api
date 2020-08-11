# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class casePrecondition(mysqlpool.Model):
    __tablename__ = "casePrecondition"
    # 定义column
    id = mysqlpool.Column(
        name="id",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    content = mysqlpool.Column(
        name="content",
        type_=TEXT(1000),
        nullable=True
    )
    caseId = mysqlpool.Column(
        name="caseId",
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
