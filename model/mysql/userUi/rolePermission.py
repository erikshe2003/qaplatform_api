# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, DATETIME
from handler.pool import mysqlpool


class RolePermission(mysqlpool.Model):
    __tablename__ = "rolePermission"

    # 定义column
    permissionId = mysqlpool.Column(
        name="permissionId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    roleId = mysqlpool.Column(
        name="roleId",
        type_=INTEGER,
        nullable=False
    )
    functionId = mysqlpool.Column(
        name="functionId",
        type_=INTEGER,
        nullable=False
    )
    hasPermission = mysqlpool.Column(
        name="hasPermission",
        type_=TINYINT(1),
        nullable=False
    )
    permissionAddTime = mysqlpool.Column(
        name="permissionAddTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    permissionUpdateTime = mysqlpool.Column(
        name="permissionUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
