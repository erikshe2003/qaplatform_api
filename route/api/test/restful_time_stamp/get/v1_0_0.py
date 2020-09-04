# -*- coding: utf-8 -*-

import time

"""
    application/json
    测试接口
"""


def time_stamp_get():
    # 初始化返回内容
    response_json = {
        "code": 200,
        "msg": "操作成功",
        "data": {
            "timestamp": time.time()
        }
    }

    return response_json
