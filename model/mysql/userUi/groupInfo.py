# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import INTEGER, TINYINT, DATETIME, VARCHAR, TEXT
from handler.pool import mysqlpool


class GroupInfo(mysqlpool.Model):
    __tablename__ = "groupInfo"
    __bind_key__ = "userUi"
    # 定义column
    groupId = mysqlpool.Column(
        name="groupId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    groupName = mysqlpool.Column(
        name="groupName",
        type_=VARCHAR(100),
        nullable=False
    )
    groupDescription = mysqlpool.Column(
        name="groupDescription",
        type_=TEXT,
        nullable=True
    )
    groupStatus = mysqlpool.Column(
        name="groupStatus",
        type_=TINYINT(1),
        nullable=False
    )
    groupAddTime = mysqlpool.Column(
        name="groupAddTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    groupUpdateTime = mysqlpool.Column(
        name="groupUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
