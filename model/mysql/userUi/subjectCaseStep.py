# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class subjectCaseStep(mysqlpool.Model):
    __tablename__ = "subjectCaseStep"
    # 定义column
    stepId = mysqlpool.Column(
        name="stepId",
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
    sequence = mysqlpool.Column(
        name="sequence",
        type_=INTEGER,
        nullable=False
    )
    stepContent = mysqlpool.Column(
        name="stepContent",
        type_=VARCHAR(255),
        nullable=False
    )
    stepExpectation = mysqlpool.Column(
        name="stepExpectation",
        type_=VARCHAR(255),
        nullable=False
    )

    stepCreateTime = mysqlpool.Column(
        name="stepCreateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    setpUpdateTime = mysqlpool.Column(
        name="setpUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
