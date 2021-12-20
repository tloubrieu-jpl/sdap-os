import unittest
import sys
import logging
import xarray
from sdap.data_access.drivers import S3COG
from sdap.operators import SpatialMean, EVI
import matplotlib.pyplot as plt

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

class S3COGTestCase(unittest.TestCase):

    def test_small_get(self):
        s3_cog_driver = S3COG()

        lat_range = [42.303, 43.326]
        lon_range = [-72.572, -71.183]
        time_range = ['2017-05-20T00:00:00.000000+00:00', '2017-06-20T00:00:00.000000+00:00']

        xas = s3_cog_driver.get_all(lon_range, lat_range, time_range, SpatialMean())

        self.plot(xas)

    #TODO enable plot as a callback of the get all function, to be able to update a plot while data is fetched
    def plot(self, results: xarray.DataArray):
        for x in results.x:
            for y in results.y:
                ts = results.sel({'x': x.values.item(), 'y': y.values.item(), 'band': 1})
                ts.plot.scatter('time', 'var')
        plt.show()

    def test_bigger_get(self):
        s3_cog_driver = S3COG()

        lat_range = [42.1, 42.6]
        lon_range = [-72.0, -71.5]
        time_range = ['2017-01-01T00:00:00.000000+00:00', '2019-01-01T00:00:00.000000+00:00']

        xas = s3_cog_driver.get_all(lon_range, lat_range, time_range, SpatialMean())
        plt.plot(xas.time, xas['var'].data[0,0,:,:])
        plt.show()

    def test_bigger_get_evi(self):
        s3_cog_driver = S3COG()

        lat_range = [42.1, 42.6]
        lon_range = [-72.0, -71.5]
        time_range = ['2017-01-01T00:00:00.000000+00:00', '2019-01-01T00:00:00.000000+00:00']

        evi = EVI(numerator_coeff=[0, 0, -2.5, 2.5, 0, 0, 0],
                  denominator_coeff=[0, 0, 2.4, 1, 0, 0, 1])

        xas = s3_cog_driver.get_all(lon_range, lat_range, time_range, evi)
        plt.plot(xas.time, xas['var'].data[0, 0, :, :])
        plt.show()

if __name__ == '__main__':
    unittest.main()
