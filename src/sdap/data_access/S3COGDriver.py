import sys
import logging
import itertools
import boto3
import rioxarray
import xarray
import ray
import rasterio as rio
from rasterio.session import AWSSession
from rasterio.errors import RasterioIOError

from pyproj import Transformer, CRS

from sdap.data_access.index.spatial import Sentinel2Grid
from sdap.data_access.index.temporal import Daily

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class S3COGDriver:

    def __init__(self,
                 region='us-west-2',
                 bucket='aqacf-nexus-stage',
                 key_pattern='hls_cog/s1_output_latlon_HLS_S30_{spatial_key}_{temporal_key}_cog.tif',
                 spatial_index=Sentinel2Grid(),
                 temporal_index=Daily(format="%Y%j")):

        self.session = boto3.Session()

        self.bucket = bucket
        self.region = region
        self.crs_tile = CRS.from_epsg(3450)

        self.key_pattern = key_pattern
        self.spatial_index = spatial_index
        self.temporal_index = temporal_index

    def get_from_key(self, spatial_key, temporal_key, x_range, y_range):

        key = self.key_pattern.format(
            spatial_key=spatial_key,
            temporal_key=temporal_key
        )
        path = f's3://{self.bucket}/{key}'

        try:
            with rio.Env(AWSSession(self.session)):
                logger.info("try to fetch %s", path)
                with rio.open(path) as f:
                    rds = rioxarray.open_rasterio(f)
                    mask_x = (rds.x >= x_range[0]) & (rds.x <= x_range[1])
                    mask_y = (rds.y >= y_range[0]) & (rds.y <= y_range[1])
                    cropped_ds = rds.where(mask_x & mask_y, drop=True)
                    transposed_ds = cropped_ds.transpose("x", "y", "band")

                    time_ds = transposed_ds.expand_dims(
                        {'time': [self.temporal_index.get_datetime(temporal_key)]},
                        axis=0
                    )
                    time_ds.name = 'var'
            return time_ds

        except RasterioIOError:
            logger.debug("object not found from key %s, ignore", key)
            return None

    def get_keys(self, x_range, y_range, t_range):
        spatial_sub_keys = self.spatial_index.get_codes(x_range, y_range)
        logger.info('spatial sub keys: %s', ', '.join(spatial_sub_keys))

        temporal_sub_keys = self.temporal_index.get_codes(t_range)
        logger.info('temporal sub keys: %s', ', '.join(temporal_sub_keys))

        return itertools.product(spatial_sub_keys, temporal_sub_keys)

    def get(self, lon_range, lat_range, t_range):

        coord_transformer = Transformer.from_crs("epsg:4326", self.crs_tile)
        # coordinates are reversed here because x, y are in wgs84
        coord_lower_left = coord_transformer.transform(lat_range[0], lon_range[0])
        coord_upper_right = coord_transformer.transform(lat_range[1], lon_range[1])
        x_range = sorted([coord_lower_left[0], coord_upper_right[0]])
        y_range = sorted([coord_lower_left[1], coord_upper_right[1]])

        ray.init(_node_ip_address='192.168.1.89', ignore_reinit_error=True)

        #@ray.remote
        def remote_partial(args_dict):
            return self.get_from_key(
                **args_dict,
                x_range=x_range,
                y_range=y_range,
            )

        #results = ray.get([remote_partial.remote({'spatial_key': s_key, 'temporal_key': t_key})
        #                   for s_key, t_key in self.get_keys(lon_range, lat_range, t_range)])

        results = []
        for s_key, t_key in self.get_keys(lon_range, lat_range, t_range):
            results.append(remote_partial({'spatial_key': s_key, 'temporal_key': t_key}))

        return xarray.merge([r for r in results if not r is None])



