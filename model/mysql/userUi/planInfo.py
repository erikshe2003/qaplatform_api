# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME
from handler.pool import mysqlpool


class PlanInfo(mysqlpool.Model):
    __tablename__ = "planInfo"
    # 定义column
    planId = mysqlpool.Column(
        name="planId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    ownerId = mysqlpool.Column(
        name="ownerId",
        type_=INTEGER,
        nullable=False
    )
    planType = mysqlpool.Column(
        name="planType",
        type_=TINYINT,
        nullable=False
    )
    planTitle = mysqlpool.Column(
        name="planTitle",
        type_=VARCHAR(50),
        nullable=False
    )
    planDescription = mysqlpool.Column(
        name="planDescription",
        type_=VARCHAR(200),
        nullable=True
    )
    planOpenLevel = mysqlpool.Column(
        name="planOpenLevel",
        type_=TINYINT,
        nullable=False
    )
    planOwnerType = mysqlpool.Column(
        name="planOwnerType",
        type_=TINYINT,
        nullable=False
    )
    forkFrom = mysqlpool.Column(
        name="forkFrom",
        type_=INTEGER,
        nullable=True
    )
    planAddTime = mysqlpool.Column(
        name="planAddTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    planUpdateTime = mysqlpool.Column(
        name="planUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    status = mysqlpool.Column(
        name="status",
        type_=TINYINT,
        nullable=False,
        default=1
    )
