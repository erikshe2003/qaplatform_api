# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME
from handler.pool import mysqlpool


class PlanType(mysqlpool.Model):
    __tablename__ = "planType"
    # 定义column
    typeId = mysqlpool.Column(
        name="typeId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    typeName = mysqlpool.Column(
        name="typeName",
        type_=VARCHAR(50),
        nullable=False
    )
    typeDescription = mysqlpool.Column(
        name="typeDescription",
        type_=VARCHAR(200),
        nullable=True
    )
    typeAddTime = mysqlpool.Column(
        name="typeAddTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    typeUpdateTime = mysqlpool.Column(
        name="typeUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
