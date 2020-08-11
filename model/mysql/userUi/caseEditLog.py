# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class caseEditLog(mysqlpool.Model):
    __tablename__ = "caseEditLog"
    # 定义column
    id = mysqlpool.Column(
        name="id",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    caseId = mysqlpool.Column(
        name="caseId",
        type_=TINYINT(4),
        nullable=False
    )
    type = mysqlpool.Column(
        name="type",
        type_=TINYINT(4),
        nullable=False
    )
    before = mysqlpool.Column(
        name="before",
        type_=TEXT(1000),
        nullable=True
    )

    after = mysqlpool.Column(
        name="after",
        type_=TEXT(1000),
        nullable=True
    )

    createTime = mysqlpool.Column(
        name="createTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
