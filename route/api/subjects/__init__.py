# -*- coding: utf-8 -*-

from flask import Blueprint
from flask_restful import Api

from .subjects import subjects

api_subjects = Blueprint('api_subjects', __name__)

api = Api(api_subjects)

api.add_resource(subjects, '/subjects.json')
