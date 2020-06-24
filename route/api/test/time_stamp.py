# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_time_stamp.get import time_stamp_get


class TimeStamp(Resource):
    def get(self):
        return time_stamp_get()
