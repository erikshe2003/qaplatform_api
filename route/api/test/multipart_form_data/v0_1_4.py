# -*- coding: utf-8 -*-

import flask
import json
import time
import random
import gevent

from route.api.test import api_test

"""
    multipart/form-data
    测试接口
"""


@api_test.route('/multipartFormData.json', methods=['get', 'post'])
def multipart_form_data():
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
