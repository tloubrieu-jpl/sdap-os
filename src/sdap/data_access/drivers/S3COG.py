import sys
import logging
import time
import itertools
import boto3
import botocore
import xarray
import ray
import numpy as np
import rioxarray
import rasterio as rio
from rasterio.session import AWSSession
from rasterio.errors import RasterioIOError

from pyproj import Transformer, CRS

from sdap.data_access.index.spatial import Sentinel2Grid
from sdap.data_access.index.temporal import Daily
from sdap.operators import OperatorProcessingException
from .Key import Key

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('rasterio').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('fiona').setLevel(logging.WARNING)

#TODO have abstract objects for spatial_index and temporal_index, instead of Daily used here
@ray.remote(max_retries=0)
def get_from_key(key: Key, x_range, y_range, operator,
                 bucket: str, session: boto3.Session, temporal_index: Daily):
    path = f's3://{bucket}/{key.get_str()}'

    try:
        result = None
        with rio.Env(AWSSession(session)):
            logger.debug("fetching %s", path)
            with rio.open(path) as f:
                rds = rioxarray.open_rasterio(f)
                mask_x = (rds.x >= x_range[0]) & (rds.x <= x_range[1])
                mask_y = (rds.y >= y_range[0]) & (rds.y <= y_range[1])
                cropped_ds = rds.where(mask_x & mask_y, drop=True)
                cropped_ds.data[cropped_ds.data == cropped_ds._FillValue] = np.nan
                if not np.isnan(cropped_ds.data).all():
                    time_ds = cropped_ds.expand_dims(
                        {'time': [temporal_index.get_datetime(key.temporal_key)]},
                        axis=0
                    )
                    time_ds.name = 'var'
                    result = operator.tile_calc(time_ds)
                else:
                    logger.debug("no valid data in subset for key %s, ignore", key)
        return result

    except RasterioIOError:
        logger.debug("object not found from key %s, ignore", key)
        return None
    except OperatorProcessingException:
        logger.debug("operator fail on key %s, ignore", key)
        return None


class S3COG:

    def __init__(self,
                 region='us-west-2',
                 bucket='aqacf-nexus-stage',
                 # TODO accept multiple key_pattern,
                 # 'hls_cog/s1_output_latlon_HLS_S30_T{spatial_key}_{temporal_key}_cog.tif' should also work
                 key_pattern=[
                     'hls_cog/s1_output_latlon_HLS_L30_T{spatial_key}_{temporal_key}_cog.tif',
                     'hls_cog/s1_output_latlon_HLS_S30_T{spatial_key}_{temporal_key}_cog.tif'
                     ],
                 spatial_index=Sentinel2Grid(),
                 temporal_index=Daily(format="%Y%j")):

        self.session = boto3.Session()

        self.bucket = bucket
        self.region = region
        self.crs_tile = CRS.from_epsg(3450)

        self.key_pattern = key_pattern
        self.spatial_index = spatial_index
        self.temporal_index = temporal_index

    def get_keys(self, x_range, y_range, t_range):
        spatial_sub_keys = self.spatial_index.get_codes(x_range, y_range)
        logger.info('spatial sub keys: %s', ', '.join(spatial_sub_keys))

        temporal_sub_keys = self.temporal_index.get_codes(t_range)
        logger.info('temporal sub keys: %s', ', '.join(temporal_sub_keys))

        s3_session = boto3.resource('s3')
        tested = 0
        found = 0
        for key_args in itertools.product(self.key_pattern ,spatial_sub_keys, temporal_sub_keys):
            tested += 1
            key = Key(*key_args)
            logger.debug("Test if key %s exists", key.get_str())
            if self.key_exists(key, s3_session):
                found += 1
                yield key
        logger.info("%i keys tested, %i keys found", tested, found)

    def key_exists(self, key: Key, s3_session):
        try:
            s3_session.Object(
                self.bucket,
                key.get_str()
            ).load()
            return True
        except botocore.exceptions.ClientError as e:
            return False

    def get_all(self, lon_range, lat_range, t_range, operator):
        xas = xarray.DataArray()
        xas.name = 'var'
        for xa in self.get(lon_range, lat_range, t_range, operator):
            xas = operator.consolidate([xas, xa])
        return xas

    def get(self, lon_range, lat_range, t_range, operator):

        coord_transformer = Transformer.from_crs("epsg:4326", self.crs_tile)
        # coordinates are reversed here because x, y are in wgs84
        coord_lower_left = coord_transformer.transform(lat_range[0], lon_range[0])
        coord_upper_right = coord_transformer.transform(lat_range[1], lon_range[1])
        x_range = sorted([coord_lower_left[0], coord_upper_right[0]])
        y_range = sorted([coord_lower_left[1], coord_upper_right[1]])

        # ray.init(_node_ip_address='128.149.255.29', ignore_reinit_error=True)
        ray.init(include_dashboard=True,
                 ignore_reinit_error=True)

        futures = {}
        for key in self.get_keys(lon_range, lat_range, t_range):
            args = {
                'key': key,
                'x_range': x_range,
                'y_range': y_range,
                'operator': operator,
                'bucket': self.bucket,
                'session': self.session,
                'temporal_index': self.temporal_index
            }
            futures[key.get_str()] = get_from_key.remote(**args)

        while futures:
            done_keys = set()
            for key_str, future in futures.items():
                if future.future().done():
                    result = future.future().result()
                    if result is not None:
                        yield result
                    done_keys.add(key_str)
            [futures.pop(key_str) for key_str in done_keys]
            time.sleep(2)

        ray.shutdown()

        #results = []
        #for s_key, t_key in self.get_keys(lon_range, lat_range, t_range):
        #    results.append(remote_partial({'spatial_key': s_key, 'temporal_key': t_key}))

        #return xarray.merge([r for r in results if not r is None])



