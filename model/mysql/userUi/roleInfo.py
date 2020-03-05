# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME, TEXT
from handler.pool import mysqlpool


class RoleInfo(mysqlpool.Model):
    __tablename__ = "roleInfo"
    # 定义column
    roleId = mysqlpool.Column(
        name="roleId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    roleName = mysqlpool.Column(
        name="roleName",
        type_=VARCHAR(20),
        nullable=False
    )
    roleDescription = mysqlpool.Column(
        name="roleDescription",
        type_=TEXT,
        nullable=True
    )
    roleIsAdmin = mysqlpool.Column(
        name="roleIsAdmin",
        type_=TINYINT(1),
        nullable=False
    )
    roleStatus = mysqlpool.Column(
        name="roleStatus",
        type_=TINYINT(1),
        nullable=False
    )
    roleAddTime = mysqlpool.Column(
        name="roleAddTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    roleUpdateTime = mysqlpool.Column(
        name="roleUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
