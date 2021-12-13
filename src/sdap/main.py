import argparse
import os
import logging
from sdap.data_access import CollectionLoader

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    cwd = os.path.dirname(__file__)
    conf_rel_path = './test/data_access/collection-config.yaml'
    parser.add_argument("conf", default=os.path.join(cwd, conf_rel_path))
    parser.add_argument("collection", default="hls")
    parser.add_argument("lon_range", nargs=2, default=[-72.572, -71.183])
    parser.add_argument("lat_range", nargs=2, default=[42.303, 43.326])
    parser.add_argument("time_range", nargs=2,
                        default=['2017-01-01T00:00:00.000000+00:00', '2017-06-01T00:00:00.000000+00:00'])

    args = parser.parse_args()

    collection_loader = CollectionLoader(args.conf)
    driver = collection_loader.get_driver(args.collection)
    result = driver.get(args.lon_range, args.lat_range, args.time_range)


if __name__ == '__main__':
    main()
