# -*- coding: utf-8 -*-


from flask_restful import Resource


from .restful_worker.post import worker_post


class Worker(Resource):
    def post(self):
        return worker_post()
