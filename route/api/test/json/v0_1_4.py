# -*- coding: utf-8 -*-

import flask
import json
import time
import gevent
import random


from route.api.test import api_test

"""
    application/json
    测试接口
"""


@api_test.route('/json.json', methods=['get', 'post'])
def test_json():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {
            "timestamp": time.time()
        }
    }

    gevent.sleep(float('%.2f' % (random.random() * 2)))

    return json.dumps(response_json)
