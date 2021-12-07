import sys
import logging
import itertools
import numpy as np
import boto3
from botocore.client import Config


import rasterio as rio
from rasterio.session import AWSSession
from rasterio.windows import Window
from rasterio.errors import RasterioIOError

from pyproj import Transformer, CRS

from sdap.data_access.index.spatial import MGRS
from sdap.data_access.index.temporal import Daily

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class S3COGDriver:

    def __init__(self,
                 region='us-west-2',
                 bucket='aqacf-nexus-stage',
                 key_prefix='hls_cog/s1_output_latlon_HLS_S30_',
                 spatial_index=MGRS(level=5),
                 temporal_index=Daily(format="%Y%j")):

        self.session = boto3.Session(region_name=region)

        self.bucket = bucket
        self.crs_tile = CRS.from_epsg(3450)

        self.key_prefix = key_prefix
        self.spatial_index = spatial_index
        self.key_separator = '_'
        self.temporal_index = temporal_index
        self.key_suffix = '_cog.tif'

    @staticmethod
    def _crop_value(v, max_v):
        return min(max_v, max(0, v))

    @staticmethod
    def _crop_window_in_shape(shape, pixel_lower_left, pixel_upper_right):

        pixel_lower_left[0] = S3COGDriver._crop_value(pixel_lower_left[0], shape[0])
        pixel_lower_left[1] = S3COGDriver._crop_value(pixel_lower_left[1], shape[1])

        pixel_upper_right[0] = S3COGDriver._crop_value(pixel_upper_right[0], shape[0])
        pixel_upper_right[1] = S3COGDriver._crop_value(pixel_upper_right[1], shape[1])

        return pixel_lower_left, pixel_upper_right

    @staticmethod
    def _get_index_window(f, coord_lower_left, coord_upper_right):

        pixel_lower_left = f.index(*coord_lower_left)
        pixel_upper_right = f.index(*coord_upper_right)

        pixel_lower_left_cropped, pixel_upper_right_cropped = S3COGDriver._crop_window_in_shape(f.shape, list(pixel_lower_left), list(pixel_upper_right))

        window = Window.from_slices(
            (pixel_upper_right_cropped[0], pixel_lower_left_cropped[0]),
            (pixel_lower_left_cropped[1], pixel_upper_right_cropped[1]))

        return window

    def get(self, x_range, y_range, t_range):
        spatial_sub_keys = self.spatial_index.get_codes(x_range, y_range)
        logger.info('spatial sub keys: %s', ', '.join(spatial_sub_keys))

        temporal_sub_keys = self.temporal_index.get_codes(t_range)
        logger.info('temporal sub keys: %s', ', '.join(temporal_sub_keys))

        key_components = itertools.product(spatial_sub_keys, temporal_sub_keys)

        keys = [self.key_prefix + kc[0] + self.key_separator + kc[1] + self.key_suffix for kc in key_components]
        logger.info('key prefixes: %s', ', '.join(keys))

        coord_transformer = Transformer.from_crs("epsg:4326", self.crs_tile)
        # coordinates are reverse here because x, y are in wgs84
        # TODO: make that consistent x,y no proj hardcoded or lat,lon
        coord_lower_left = coord_transformer.transform(y_range[0], x_range[0])
        coord_upper_right = coord_transformer.transform(y_range[1], x_range[1])

        time = []
        results = []

        for kc in key_components:
            try:
                key = self.key_prefix + kc[0] + self.key_separator + kc[1] + self.key_suffix
                path = f's3://{self.bucket}/{key}'
                with rio.Env(AWSSession(self.session)):
                    logger.info("try to fetch %s", path)
                    with rio.open(path) as f:

                        # calculate pixels to be streamed in cog
                        window = S3COGDriver._get_index_window(f, coord_lower_left, coord_upper_right)
                        img = f.read(window=window)
                        img[img == -3.4e+38] = np.nan
                        if not np.isnan(img).all():
                            time.append(self.temporal_index.get_datetime(kc[1]))
                            results.append(img)

            except RasterioIOError as e:
                logger.debug("object not found, ignore")

        return time, results



