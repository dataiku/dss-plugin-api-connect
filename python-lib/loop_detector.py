import copy


class LoopDetector():
    def __init__(self):
        self.previous_url = None
        self.previous_params = None
        self.previous_headers = None

    def is_stuck_in_loop(self, url, params, headers):
        if url == self.previous_url \
           and params == self.previous_params \
           and headers == self.previous_headers:
            return True
        self.previous_url = url
        self.previous_params = copy.deepcopy(params)
        self.previous_headers = copy.deepcopy(headers)
        return False
