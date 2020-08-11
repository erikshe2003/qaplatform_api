# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class subject(mysqlpool.Model):
    __tablename__ = "subject"
    # 定义column
    subjectId = mysqlpool.Column(
        name="subjectId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    userId = mysqlpool.Column(
        name="userId",
        type_=INTEGER,
        nullable=False
    )
    subjectStatus = mysqlpool.Column(
        name="subjectStatus",
        type_=TINYINT(4),
        nullable=False
    )
    subjectOpenLevel = mysqlpool.Column(
        name="subjectOpenLevel",
        type_=TINYINT(4),
        nullable=False
    )
    subjectName = mysqlpool.Column(
        name="subjectName",
        type_=VARCHAR(50),
        nullable=False
    )
    subjectDescription = mysqlpool.Column(
        name="subjectDescription",
        type_=TEXT,
        nullable=True
    )
    subjectLogoPath = mysqlpool.Column(
        name="subjectLogoPath",
        type_=TEXT,
        nullable=True
    )

    subjectCreateTime = mysqlpool.Column(
        name="subjectCreateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    subjectUpdateTime = mysqlpool.Column(
        name="subjectUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
