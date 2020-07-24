# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class caseFile(mysqlpool.Model):
    __tablename__ = "caseFile"
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

    ossPath = mysqlpool.Column(
        name="ossPath",
        type_=TEXT(1000),
        nullable=False
    )

    fileAlias = mysqlpool.Column(
        name="fileAlias",
        type_=TEXT(1000),
        nullable=True
    )
    status = mysqlpool.Column(
        name="status",
        type_=TINYINT(4),
        nullable=False
    )

    userId = mysqlpool.Column(
        name="userId",
        type_=TINYINT(4),
        nullable=False
    )

    createTime = mysqlpool.Column(
        name="createTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )


