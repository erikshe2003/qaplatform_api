# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class subjectCasePrecondition(mysqlpool.Model):
    __tablename__ = "subjectCasePrecondition"
    # 定义column
    preconditionId = mysqlpool.Column(
        name="preconditionId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    caseId = mysqlpool.Column(
        name="caseId",
        type_=INTEGER,
        nullable=False
    )
    catalogueId = mysqlpool.Column(
        name="catalogueId",
        type_=INTEGER,
        nullable=False
    )
    subjectId = mysqlpool.Column(
        name="subjectId",
        type_=INTEGER,
        nullable=False
    )

    preconditionContent = mysqlpool.Column(
        name="preconditionContent",
        type_=VARCHAR(255),
        nullable=False
    )

    preconditionCreateTime = mysqlpool.Column(
        name="preconditionCreateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    preconditionUpdateTime = mysqlpool.Column(
        name="preconditionUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
