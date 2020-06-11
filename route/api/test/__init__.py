# -*- coding: utf-8 -*-

from flask import Blueprint
from flask_restful import Api

from .time_stamp import TimeStamp

api_test = Blueprint('api_test', __name__)
api = Api(api_test)
api.add_resource(TimeStamp, '/timeStamp.json')
