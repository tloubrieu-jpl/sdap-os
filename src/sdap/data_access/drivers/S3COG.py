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
from sdap.utils import get_log
from .Key import Key

logger = get_log(__name__)

logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('rasterio').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)



def convert_coordinates(xas, target_crs="epsg:4326"):
    xv, yv = np.meshgrid(xas.x, xas.y)

    transformer = Transformer.from_crs(CRS(xas.spatial_ref.crs_wkt),
                                       target_crs,
                                       always_xy=True,
                                       )

    request_x, request_y = transformer.transform(xv, yv)
    xas.coords['request_x'] = (('x', 'y'), request_x)
    xas.coords['request_y'] = (('x', 'y'), request_y)
    # xas.attrs['spatial_ref'] = '+init=epsg:4326'
    return xas


#TODO have abstract objects for spatial_index and temporal_index, instead of Daily used here
@ray.remote(max_retries=0)
def get_from_key(key: Key, x_range, y_range, crs, operator,
                 bucket: str, session: boto3.Session, temporal_index: Daily):
    path = f's3://{bucket}/{key.get_str()}'

    try:
        result = None
        with rio.Env(AWSSession(session)):
            logger.debug("fetching %s", path)
            with rio.open(path) as f:
                rds = rioxarray.open_rasterio(f)
                rds = convert_coordinates(rds, crs)
                mask_x = (rds.request_x >= x_range[0]) & (rds.request_x <= x_range[1])
                mask_y = (rds.request_y >= y_range[0]) & (rds.request_y <= y_range[1])
                rds = rds.where(mask_x & mask_y, drop=True)
                rds.data[rds.data == rds._FillValue] = np.nan
                if not np.isnan(rds.data).all():
                    rds = rds.expand_dims(
                        {'time': [temporal_index.get_datetime(key.temporal_key)]},
                        axis=0
                    )
                    rds.name = 'var'
                    result = operator.tile_calc(rds)
                    del rds
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

    def get_keys(self, x_range, y_range, crs, t_range):

        spatial_sub_keys = self.spatial_index.get_codes(x_range, y_range, crs)
        logger.info('spatial sub keys: %s', ', '.join(spatial_sub_keys))


        temporal_sub_keys = self.temporal_index.get_codes(t_range)
        logger.info('temporal sub keys: %s', ', '.join(temporal_sub_keys))

        s3_session = boto3.resource('s3')
        tested = 0
        found = 0
        for key_args in itertools.product(self.key_pattern, spatial_sub_keys, temporal_sub_keys):
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

    def get_all(self, request_x_range, request__y_range, t_range, operator, crs="epsg:4326"):
        xas = xarray.DataArray()
        xas.name = 'var'
        for xa in self.get(request_x_range, request__y_range, t_range, operator, request_crs="epsg:4326"):
            xas = operator.consolidate([xas, xa])
            del xa

        return xas

    def get(self, request_x_range, request_y_range, t_range, operator, request_crs="epsg:4326"):

        # ray.init(_node_ip_address='128.149.255.29', ignore_reinit_error=True)
        ray.init(include_dashboard=True,
                 ignore_reinit_error=True,
                 #local_mode=True
                 )

        futures = {}
        for key in self.get_keys(request_x_range, request_y_range, request_crs, t_range):
            args = {
                'key': key,
                'x_range': request_x_range,
                'y_range': request_y_range,
                'crs': request_crs,
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




