# -*- coding: utf-8 -*-

from flask import Blueprint
from flask_restful import Api

from .subject import subject

api_subject = Blueprint('api_subject', __name__)

api = Api(api_subject)

api.add_resource(subject, '/subject.json')
