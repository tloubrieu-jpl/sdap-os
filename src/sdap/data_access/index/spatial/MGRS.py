import mgrs


class MGRS:

    def __init__(self, level=20):
        self.level = level
        self.m = mgrs.MGRS()

    def get_codes(self, lon_range, lat_range):
        # to be revised
        #min_code = self.m.toMGRS(lat_range[0], lon_range[0], MGRSPrecision=self.level)
        #max_code = self.m.toMGRS(lat_range[1], lon_range[1], MGRSPrecision=self.level)
        #return [min_code, max_code]
        return ['T18TYN']

