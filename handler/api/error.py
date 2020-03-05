# -*- coding: utf-8 -*-

import json

from handler.log import api_logger


class ApiError:
    # 请求操作失败的方法
    @classmethod
    def requestfail_error(cls, msg):
        api_logger.error("请求操作失败：" + msg)
        response_json = {
            "error_code": 201,
            "error_msg": msg,
            "data": {}
        }
        response = json.dumps(response_json)
        return response

    # 缺少必传项的方法
    @classmethod
    def requestfail_nokey(cls, msg):
        api_logger.error("缺少必传项：" + msg)
        response_json = {
            "error_code": 302,
            "error_msg": "缺少必传参数",
            "data": {}
        }
        response = json.dumps(response_json)
        return response

    # 服务处理异常
    @classmethod
    def requestfail_server(cls, msg):
        api_logger.error("服务处理异常：" + msg)
        response_json = {
                "error_code": 500,
                "error_msg": "服务处理异常",
                "data": {}
            }
        response = json.dumps(response_json)
        return response

    # 参数传值非法的方法
    @classmethod
    def requestfail_value(cls, msg):
        api_logger.error("参数传值非法：" + msg)
        response_json = {
            "error_code": 301,
            "error_msg": "参数传值非法",
            "data": {}
        }
        response = json.dumps(response_json)
        return response
