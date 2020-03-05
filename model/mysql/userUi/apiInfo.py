# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import INTEGER, DATETIME, VARCHAR, TEXT
from handler.pool import mysqlpool


class ApiInfo(mysqlpool.Model):
    __tablename__ = "apiInfo"
    # 定义column
    apiId = mysqlpool.Column(
        name="apiId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    apiName = mysqlpool.Column(
        name="apiName",
        type_=VARCHAR(100),
        nullable=False
    )
    apiUrl = mysqlpool.Column(
        name="apiUrl",
        type_=VARCHAR(200),
        nullable=False
    )
    apiDescription = mysqlpool.Column(
        name="apiDescription",
        type_=TEXT,
        nullable=True
    )
    apiAddTime = mysqlpool.Column(
        name="apiAddTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
