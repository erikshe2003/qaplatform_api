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
from .caseCopy import casecopy
from .caseIndex import caseindex
from .cases import cases


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
api.add_resource(casecopy, '/caseCopy.json')
api.add_resource(caseindex, '/caseIndex.json')
api.add_resource(cases, '/cases.json')