import xarray
import numpy as np


class EVI:

    def __init__(self, numerator_coeff: [float] = None, denominator_coeff: [float] = None, dimension='band'):
        '''

        :param numerator_coeff: list of float which length is length of the dimension 'dimension' +1
        :param denominator_coeff: list of float which length is length of the dimension 'dimension' +1
        :param dimension:
        '''
        self.numerator_coeff = numerator_coeff
        self.demominator_coeff = denominator_coeff
        self.dimension = dimension

    def consolidate(self, inputs: [xarray.DataArray]):
        combined_inputs = inputs[0]
        for i in range(len(inputs))[1:]:
            combined_inputs = combined_inputs.combine_first(inputs[i])

        return combined_inputs

    def tile_calc(self, input: xarray.DataArray):

        def linear(coeff, bands):
            linear_sum = 0
            for i in range(len(bands)):
                if not np.isnan(bands[i]):
                    linear_sum += bands[i] * coeff[i]
                elif coeff[i] != 0:
                    return np.nan

            return coeff[-1] + linear_sum

        def evi(bands, axis=None):
            #TODO sort bands values per axis
            numerator = linear(self.numerator_coeff, bands)
            if self.demominator_coeff:
                return numerator / linear(self.demominator_coeff, bands)
            else:
                return numerator


        return input.reduce(evi, dim = ['time', 'x', 'y'])

