# -*- coding: utf-8 -*-

from flask import Blueprint


api_management_user = Blueprint("api_management_user", __name__)

# 加载具体路由
from .getUserList import get_user_list
from .searchUser import search_user
from .changeUserRole import change_user_role
from .forbiddenUser import forbidden_user
from .deleteUser import delete_user
