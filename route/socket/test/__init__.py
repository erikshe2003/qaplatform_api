# -*- coding: utf-8 -*-

from flask import Blueprint

ws_test = Blueprint('ws_test', __name__)

# 加载具体路由
from route.socket.test.websocket import echo_socket
