import unittest
from sdap.data_access import S3COGDriver


class MyTestCase(unittest.TestCase):
    def test_get(self):
        s3_cog_driver = S3COGDriver()

        lat_range = [42.0, 43.0]
        lon_range = [-72.0, -71.0]
        time_range = ['2017-01-01T00:00:00.000000+00:00', '2017-06-01T00:00:00.000000+00:00']

        time, result = s3_cog_driver.get(lon_range, lat_range, time_range)

        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
