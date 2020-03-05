# -*- coding: utf-8 -*-

from flask import Blueprint


user_apis = Blueprint("user_apis", __name__)

# 加载具体路由
from route.api.user.login import login_json
from route.api.user.infoConfirm import info_confirm
from route.api.user.checkPermission import check_permission
from route.api.user.checkToken import check_token
from route.api.user.registerApply import register_apply
from route.api.user.resetPasswordApply import reset_password_apply
from route.api.user.resetPassword import reset_password
from route.api.user.recordCodeCheck import record_code_check
from route.api.user.setBaseInfo import set_base_info
from route.api.user.getBaseInfo import get_base_info
from route.api.user.changeMail import change_mail
from route.api.user.modifyPassword import modify_password
