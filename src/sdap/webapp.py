import os
import argparse
from datetime import datetime

from flask import Flask
from flask_restful import Resource, Api, reqparse

from sdap.data_access import CollectionLoader

from sdap.utils import get_log

from sdap.webapp_resources import Home
from sdap.webapp_resources import Collections
from sdap.webapp_resources import CollectionById

logger = get_log(__name__)


class Operators(Resource):

    def __init__(self, **kwargs):
        self._collection_loader = kwargs['collection_loader']

    def get(self):
        return "to be implemented"


class Jobs(Resource):

    def __init__(self, **kwargs):
        self._collection_loader = kwargs['collection_loader']

    def get(self):
        return "to be implemented"


def create_parser():

    server_cmd_parser = argparse.ArgumentParser()
    cwd = os.path.dirname(__file__)
    conf_rel_path = './test/data_access/collection-config.yaml'
    server_cmd_parser.add_argument("--conf", required=False, default=os.path.join(cwd, conf_rel_path))
    server_cmd_parser.add_argument("--secrets", required=False, default=None)
    return server_cmd_parser


if __name__ == '__main__':

    parser = create_parser()
    args = parser.parse_args()
    collection_loader = CollectionLoader(args.conf, secret_file=args.secrets)

    app = Flask('sdap.webapp')
    app.config['BUNDLE_ERRORS'] = True
    api = Api(app)

    api.add_resource(Home, '/')

    api.add_resource(
         Collections,
         '/collections',
         resource_class_kwargs={'collection_loader': collection_loader}
    )

    api.add_resource(
        CollectionById,
        '/collections/<string:collection_id>',
        resource_class_kwargs={'collection_loader': collection_loader}
    )

    app.run(host='0.0.0.0', port=8083, debug=True)