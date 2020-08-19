# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.mysql import TINYINT, INTEGER, VARCHAR, DATETIME
from handler.pool import mysqlpool


class UserInfo(mysqlpool.Model):
    __tablename__ = "userInfo"
    # 定义column
    userId = mysqlpool.Column(
        name="userId",
        type_=INTEGER,
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True
    )
    userLoginName = mysqlpool.Column(
        name="userLoginName",
        type_=VARCHAR(100),
        unique=True,
        nullable=True
    )
    userNickName = mysqlpool.Column(
        name="userNickName",
        type_=VARCHAR(100),
        nullable=True
    )
    userEmail = mysqlpool.Column(
        name="userEmail",
        type_=VARCHAR(100),
        nullable=True
    )
    userPassword = mysqlpool.Column(
        name="userPassword",
        type_=VARCHAR(100),
        nullable=True
    )
    userStatus = mysqlpool.Column(
        name="userStatus",
        type_=TINYINT(1),
        nullable=False
    )
    userRoleId = mysqlpool.Column(
        name="userRoleId",
        type_=INTEGER,
        nullable=True
    )
    userIntroduction = mysqlpool.Column(
        name="userIntroduction",
        type_=VARCHAR(200),
        nullable=True
    )
    userAddTime = mysqlpool.Column(
        name="userAddTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now
    )
    userRegisterTime = mysqlpool.Column(
        name="userRegisterTime",
        type_=DATETIME,
        nullable=True
    )
    userUpdateTime = mysqlpool.Column(
        name="userUpdateTime",
        type_=DATETIME,
        nullable=False,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
    userNewEmail = mysqlpool.Column(
        name="userNewEmail",
        type_=VARCHAR(100),
        nullable=True
    )
    userHeadIconUrl = mysqlpool.Column(
        name="userHeadIconUrl",
        type_=VARCHAR(200),
        nullable=True
    )
