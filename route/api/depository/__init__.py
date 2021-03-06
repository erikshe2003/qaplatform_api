from flask import Blueprint
from flask_restful import Api

from .depository import depository
from .depositories import Depositories
from .column import column
from .cases import cases
from .case import case
from .caseFiles import caseFiles
from .caseEditLog import caseEditLog
api_depository = Blueprint('api_depository', __name__)

api = Api(api_depository)

api.add_resource(depository, '/depository.json')
api.add_resource(Depositories, '/depositories.json')
api.add_resource(column, '/column.json')
api.add_resource(cases, '/cases.json')
api.add_resource(case, '/case.json')
api.add_resource(caseFiles, '/caseFiles.json')
api.add_resource(caseEditLog, '/caseEditLog.json')
