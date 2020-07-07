# -*- coding: utf-8 -*-

from flask import Blueprint
from flask_restful import Api

from .subject import subject
from .catalogues import catalogues
from .catalogue import catalogue
from .case import case

api_subject = Blueprint('api_subject', __name__)

api = Api(api_subject)

api.add_resource(subject, '/subject.json')
api.add_resource(catalogues, '/catalogues.json')
api.add_resource(catalogue, '/catalogue.json')
api.add_resource(case, '/case.json')
