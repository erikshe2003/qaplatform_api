# -*- coding: utf-8 -*-

from flask import Blueprint

api_test = Blueprint('api_test', __name__)

# 加载具体路由
from route.api.test.x_www_form_urlencoded import x_www_form_urlencoded
from route.api.test.multipart_form_data import multipart_form_data
from route.api.test.json import test_json
from route.api.test.get import http_get
