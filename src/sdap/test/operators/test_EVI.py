import unittest
from datetime import datetime
import xarray
import math
import numpy as np
from sdap.operators import EVI


class EVITestCase(unittest.TestCase):
    input1 = xarray.Dataset(
        {
            "var": (
                ("x", "y", "time", "band"),
                np.arange(16).reshape(2, 2, 2, 2),
            )
        },
        coords={
            "x": [10, 20],
            "y": [150, 160],
            "time": [
                datetime.fromisoformat('2021-12-16'),
                datetime.fromisoformat('2021-12-17')
            ],
            "band": [1, 2]},
    )

    input2 = xarray.Dataset(
        {
            "var": (
                ("x", "y", "time", "band"),
                np.arange(16, 32).reshape(2, 2, 2, 2),
            )
        },
        coords={
            "x": [30, 40],
            "y": [150, 160],
            "time": [
                datetime.fromisoformat('2021-12-18'),
                datetime.fromisoformat('2021-12-19')
            ],
            "band": [1, 2]},
    )

    def test_consolidate(self):
        evi = EVI([1, 2, 3], [4, 5, 6])
        output1 = evi.tile_calc(self.input1)
        output2 = evi.tile_calc(self.input2)

        evi.consolidate([output1, output2])


    def test_tile_calc(self):

        evi = EVI([1, 2, 3], [4, 5, 6])

        output = evi.tile_calc(self.input1)

        expected_result = [
            [
                [0.41304348, 0.4],
                [0.390625, 0.38356164]
            ],
            [
                [0.37804878, 0.37362637],
                [0.37, 0.36697248]
            ]
        ]

        assert np.isclose(output['var'].data, np.asarray(expected_result)).all()


if __name__ == '__main__':
    unittest.main()
