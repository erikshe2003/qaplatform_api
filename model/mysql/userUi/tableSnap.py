# -*- coding: utf-8 -*-

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, MEDIUMTEXT, DATETIME
from handler.pool import mysqlpool


class TableSnap(mysqlpool.Model):
    __tablename__ = "tableSnap"
    # 定义column
    id = mysqlpool.Column(
        name="id",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    status = mysqlpool.Column(
        name="status",
        type_=TINYINT,
        nullable=False
    )
    snapAddTime = mysqlpool.Column(
        name="snapAddTime",
        type_=DATETIME,
        nullable=False
    )
    planId = mysqlpool.Column(
        name="planId",
        type_=INTEGER,
        nullable=False
    )
    table = mysqlpool.Column(
        name="table",
        type_=MEDIUMTEXT,
        nullable=True
    )
