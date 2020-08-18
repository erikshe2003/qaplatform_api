from flask import Blueprint
from flask_restful import Api

from .project import project
from .projects import projects
from .project_member import projectmember
from .project_role import projectrole
from .project_roleUser import projectroleUser
from .project_list import projectlist
from .project_column import projectcolumn
from .case import case
from .exportArchive import exportArchive
from .caseIndex import caseindex
from .cases import cases
from .caseExporFilet import caseExporFilet
from .caseReview import caseReview
from .projectArchive import projectArchive
from .caseConflict import caseConflict
api_project = Blueprint('api_project', __name__)

api = Api(api_project)

api.add_resource(project, '/project.json')
api.add_resource(projects, '/projects.json')
api.add_resource(projectmember, '/member.json')
api.add_resource(projectrole, '/role.json')
api.add_resource(projectroleUser, '/roleUser.json')
api.add_resource(projectlist, '/list.json')
api.add_resource(projectcolumn, '/column.json')
api.add_resource(case, '/case.json')
api.add_resource(exportArchive, '/exportArchive.json')
api.add_resource(caseindex, '/caseIndex.json')
api.add_resource(cases, '/cases.json')
api.add_resource(caseExporFilet, '/caseExporFilet.json')
api.add_resource(caseReview, '/caseReview.json')
api.add_resource(projectArchive, '/projectArchive.json')
api.add_resource(caseConflict,'/caseConflict.json')