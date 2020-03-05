# -*- coding: utf-8 -*-

import json
import time
import gevent
import random


from route.api.test import api_test

"""
    get
    测试接口
"""


@api_test.route('/httpGet', methods=['get'])
def http_get():
    # 初始化返回内容
    response_json = {
        "error_code": 200,
        "error_msg": "操作成功",
        "data": {
            "start_timestamp": 0.0,
            "end_timestamp": 0.0
        }
    }
    response_json['data']['start_timestamp'] = time.time()

    gevent.sleep(float('%.2f' % (random.random()/2)))

    response_json['data']['end_timestamp'] = time.time()

    return json.dumps(response_json)
