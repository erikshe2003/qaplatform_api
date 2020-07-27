from flask import Blueprint
from flask_restful import Api

from .depository import depository
from .depositorys import depositorys
from .column import column
from .cases import cases

api_depository = Blueprint('api_depository', __name__)

api = Api(api_depository)

api.add_resource(depository, '/depository.json')
api.add_resource(depositorys, '/depositorys.json')
api.add_resource(column, '/column.json')
api.add_resource(cases, '/cases.json')