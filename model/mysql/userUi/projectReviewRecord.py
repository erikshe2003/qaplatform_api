# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, DATETIME
from handler.pool import mysqlpool


class projectReviewRecord(mysqlpool.Model):
    __tablename__ = "projectReviewRecord"
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
    initiatorId = mysqlpool.Column(
        name="initiatorId",
        type_=TINYINT(4),
        nullable=False
    )
    reviewerId = mysqlpool.Column(
        name="reviewerId",
        type_=TINYINT(4),
        nullable=False
    )
    result = mysqlpool.Column(
        name="result",
        type_=TINYINT(4),
        nullable=False
    )

    createTime = mysqlpool.Column(
        name="createTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )

    finishTime = mysqlpool.Column(
        name="finishTime",
        type_=DATETIME,
        nullable=True,
        default=datetime.datetime.now
    )
