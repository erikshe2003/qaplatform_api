# -*- coding: utf-8 -*-

import json

from handler.log import api_logger


class ApiError:
    # 请求操作失败的方法
    @classmethod
    def requestfail_error(cls, msg):
        api_logger.warn("请求操作失败：" + msg)
        response_json = {
            "code": 201,
            "msg": msg,
            "data": {}
        }
        return response_json

    # 缺少必传项的方法
    @classmethod
    def requestfail_nokey(cls, msg):
        api_logger.warn("缺少必传项：" + msg)
        response_json = {
            "code": 302,
            "msg": "缺少必传参数",
            "data": {}
        }
        return response_json

    # 服务处理异常
    @classmethod
    def requestfail_server(cls, msg):
        api_logger.warn("服务处理异常：" + msg)
        response_json = {
                "code": 500,
                "msg": "服务处理异常",
                "data": {}
            }
        return response_json

    # 参数传值非法的方法
    @classmethod
    def requestfail_value(cls, msg):
        api_logger.warn("参数传值非法：" + msg)
        response_json = {
            "code": 301,
            "msg": "参数传值非法",
            "data": {}
        }
        return response_json
