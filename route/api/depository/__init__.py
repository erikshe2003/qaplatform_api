from flask import Blueprint
from flask_restful import Api

from .depository import depository


api_depository = Blueprint('api_depository', __name__)

api = Api(api_depository)

api.add_resource(depository, '/depository.json')
