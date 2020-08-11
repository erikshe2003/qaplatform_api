# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class subjectCaseCatalogue(mysqlpool.Model):
    __tablename__ = "subjectCaseCatalogue"
    # 定义column
    catalogueId = mysqlpool.Column(
        name="catalogueId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    catalogueName = mysqlpool.Column(
        name="catalogueName",
        type_=VARCHAR(255),
        nullable=False
    )
    subjectId = mysqlpool.Column(
        name="subjectId",
        type_=INTEGER,
        nullable=False
    )
    catalogueStatus = mysqlpool.Column(
        name="catalogueStatus",
        type_=TINYINT(4),
        nullable=False
    )

    catalogueCreateTime = mysqlpool.Column(
        name="catalogueCreateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    catalogueUpdateTime = mysqlpool.Column(
        name="catalogueUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
