

class Key:
    def __init__(self, pattern, s_key, t_key):
        self.pattern = pattern
        self.spatial_key = s_key
        self.temporal_key = t_key

    def get_str(self):
        return self.pattern.format(
            spatial_key=self.spatial_key,
            temporal_key=self.temporal_key
        )

