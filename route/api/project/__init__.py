from flask import Blueprint
from flask_restful import Api

from .project import project
from .projects import projects
from .projectmember import projectmember
api_project = Blueprint('api_project', __name__)

api = Api(api_project)

api.add_resource(project, '/project.json')
api.add_resource(projects, '/projects.json')
api.add_resource(projectmember, '/member.json')