# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class subjectCase(mysqlpool.Model):
    __tablename__ = "subjectCase"
    # 定义column
    caseId = mysqlpool.Column(
        name="caseId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
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
    fatherCaseId = mysqlpool.Column(
        name="fatherCaseId",
        type_=INTEGER,
        nullable=False
    )
    caseText = mysqlpool.Column(
        name="caseText",
        type_=TEXT,
        nullable=True
    )
    caseStatus = mysqlpool.Column(
        name="caseStatus",
        type_=TINYINT(4),
        nullable=False
    )
    caseType = mysqlpool.Column(
        name="caseType",
        type_=TINYINT(4),
        nullable=False
    )

    caseName = mysqlpool.Column(
        name="caseName",
        type_=VARCHAR(50),
        nullable=False
    )

    caseCreateTime = mysqlpool.Column(
        name="caseCreateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    caseUpdateTime = mysqlpool.Column(
        name="caseUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
