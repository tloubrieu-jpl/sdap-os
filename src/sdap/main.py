import argparse
import os
import sys
import json
import logging
from sdap.data_access import CollectionLoader
import numpy as np
from sdap.operators import *
import matplotlib.pyplot as plt
from matplotlib.image import imread
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from datetime import datetime, date

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


def create_parser():
    parser = argparse.ArgumentParser()
    cwd = os.path.dirname(__file__)
    conf_rel_path = './test/data_access/collection-config.yaml'
    parser.add_argument("--conf", required=False, default=os.path.join(cwd, conf_rel_path))
    parser.add_argument("--collection", required=False, default="hls")
    parser.add_argument("--lon-range", required=False, nargs=2, type=float, default=[-71.272, -71.183])
    parser.add_argument("--lat-range", required=False, nargs=2, type=float, default=[42.303, 43.316])
    parser.add_argument("--time-range", required=False, nargs=2, type=str,
                        default=['2017-01-01T00:00:00.000000+00:00', '2017-04-01T00:00:00.000000+00:00'])

    parser.add_argument("--operator-name", required=False, default="SpatialMean")
    parser.add_argument("--operator-args", type=str, required=False, default=None,
                        help="arguments used to initialize the operator, "
                             "repeat option for each argument")
    return parser


def get_operator(operator_name, operator_args):
    operator_class = globals()[operator_name]
    if operator_args:
        return operator_class(*eval(operator_args))
    else:
        return operator_class()


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def extend_range(range, margin):
    """
    :param range: bounds of the range
    :param margin: in proportion of the range, for example 0.1
    :return: extended range by the margin
    """
    actual_margin = (range[1] - range[0]) * margin
    return [range[0] - actual_margin, range[1] + actual_margin]

def plot_map(xas, lon_range, lat_range, margin):
    fig = plt.figure()
    ax = plt.axes(projection=ccrs.PlateCarree())

    # background
    ax.add_wmts('https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/wmts.cgi',
                'ASTER_GDEM_Greyscale_Shaded_Relief')

    # extent
    lon_range = extend_range(lon_range, margin)
    lat_range = extend_range(lat_range, margin)
    ax.set_extent(lon_range + lat_range, crs=ccrs.PlateCarree())

    # data
    color_map = ax.pcolormesh(xas.lon, xas.lat, xas.isel(time=0), alpha=0.5, transform=ccrs.PlateCarree())
    fig.colorbar(color_map, ax=ax)

    # graticule
    gl = ax.gridlines(linestyle=":", draw_labels=True)

    plt.show()


def main():
    parser = create_parser()
    args = parser.parse_args()

    collection_loader = CollectionLoader(args.conf)
    driver = collection_loader.get_driver(args.collection)

    operator = get_operator(args.operator_name, args.operator_args)
    result = driver.get_all(args.lon_range, args.lat_range, args.time_range, operator)
    result_str = json.dumps(result.to_dict(), default=json_serial)
    print(result_str)
    plot_map(result, args.lon_range, args.lat_range, 0.2)




if __name__ == '__main__':
    main()
