from datetime import datetime, timedelta


class Daily:
    def __init__(self, format='%Y%j'):
        self.format = format
        self.delta = timedelta(days=1)

    def get_codes(self, temporal_range):

        start_time = datetime.fromisoformat(temporal_range[0])
        end_time = datetime.fromisoformat(temporal_range[1])
        codes = []
        current_time = start_time
        while current_time < end_time:
            codes.append(current_time.strftime(self.format))
            current_time += self.delta

        return codes

    def get_datetime(self, code):
        return datetime.strptime(code, self.format)
