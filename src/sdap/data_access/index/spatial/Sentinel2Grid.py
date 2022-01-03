import logging
import fsspec
import geopandas as gpd
from shapely.geometry import Polygon
from pyproj import Transformer

logging.getLogger('fiona').setLevel(logging.WARNING)


class Sentinel2Grid:

    def __init__(self):
        gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'r'
        kml_file = 'simplecache::https://sentinel.esa.int/documents/247904/1955685/S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000_21000101T000000_B00.kml'
        with fsspec.open(kml_file) as file:
            self.tiles_df = gpd.read_file(file, driver='KML')

    def get_codes(self, x_range, y_range, crs):

        coord_transformer = Transformer.from_crs(crs, "epsg:4326")
        coord_lower_left = coord_transformer.transform(x_range[0], y_range[0])
        coord_upper_right = coord_transformer.transform(x_range[1], y_range[1])
        lon_range = sorted([coord_lower_left[0], coord_upper_right[0]])
        lat_range = sorted([coord_lower_left[1], coord_upper_right[1]])

        bbox = Polygon([
            (lon_range[0], lat_range[0]),
            (lon_range[0], lat_range[1]),
            (lon_range[1], lat_range[1]),
            (lon_range[1], lat_range[0]),
            (lon_range[0], lat_range[0])
        ])

        #Too slow
        idx = self.tiles_df[self.tiles_df.intersects(bbox)]

        return idx['Name'].array
        #return ['18TYN']

