from datetime import datetime
from flask import jsonify
from flask import request
from flask_restful import Resource
from marshmallow import Schema
from webargs import fields
from flask import current_app as app

from sdap.operators import Identity
from sdap.utils import get_operator


class CollectionsByIdQuerySchema(Schema):
    collection_id = fields.String(),
    bbox = fields.DelimitedList(fields.Float, required=True)
    crs = fields.String(required=False, default='EPSG:4326')
    time_range = fields.DelimitedList(fields.String, required=True)
    operator = fields.String(required=False, default=Identity)
    operator_args = fields.List(fields.String,  required=False, default=None)


request_schema = CollectionsByIdQuerySchema()

class CollectionById(Resource):

    def __init__(self, **kwargs):
        self._collection_loader = kwargs['collection_loader']

    def get(self, collection_id):
        app.logger.debug(request.args)
        args = request_schema.load(request.args)

        # req_parser = reqparse.RequestParser()
        # req_parser.add_argument(
        #     'bbox',
        #     type=str,
        #     required=False,
        #     help='bbox lower-left coordinates,upper-right coordinates, comma-separated values in the given CRS',
        #     default='42.303, -71.272, 43.316, -71.183'
        # )
        # req_parser.add_argument(
        #     'crs',
        #     type=str,
        #     required=False,
        #     default='EPSG:4326',
        #     help='CRS of the bbox coordinates, default is EPSG:4326: latitude,longitude'
        # )
        # req_parser.add_argument(
        #     'time-range',
        #     type=str,
        #     required=False,
        #     help="time range in ISO8601 format for example 2017-01-01T00:00:00.000000+00:00,2017-04-01T00:00:00.000000+00:00",
        #     default='2017-01-01T00:00:00.000000+00:00, 2017-04-01T00:00:00.000000+00:00'
        # )
        #
        # req_parser.add_argument(
        #     "operator-name",
        #     required=False,
        #     help="algorithm to apply on collection",
        #     default="SpatialMean",
        # )
        #
        # req_parser.add_argument(
        #     "operator-args",
        #     type=str,
        #     required=False,
        #     default=None,
        #     help="arguments used to initialize the operator, "
        #          "repeat option for each argument"
        # )

        #args = req_parser.parse_args()
        #
        app.logger.debug("get driver for collection %s", collection_id)
        driver = self._collection_loader.get_driver(collection_id)
        #
        time_range = [datetime.fromisoformat(t.strip()) for t in args['time_range']]

        operator = get_operator(args['operator'], args['operator-args'])
        result = driver.get_all(
             args['bbox'],
             time_range,
             operator,
             crs=args.crs)

        #return jsonify(result.to_dict())

        return [collection_id, args['bbox']]


