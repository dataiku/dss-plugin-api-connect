from safe_logger import SafeLogger


logger = SafeLogger("api-connect plugin Pagination")


class Pagination(object):

    def __init__(self, config=None, skip_key=None, limit_key=None, total_key=None, next_page_key=None):
        self.next_page_key = None
        self.skip_key = None
        self.limit_key = None
        self.total_key = None
        self.total = None
        self.next_page_url = None
        self.remaining_records = None
        self.records_to_skip = None
        self.pagination_type = ""
        self.counting_key = None
        self.counter = None
        self.is_last_batch_empty = None
        self.is_first_batch = None
        self.is_paging_started = None
        self.next_page_number = None

    def configure_paging(self, config=None, skip_key=None, limit_key=None, total_key=None, next_page_key=None, url=None, pagination_type="na"):
        config = {} if config is None else config
        self.limit_key = config.get("limit_key", limit_key)
        self.pagination_type = config.get("pagination_type", pagination_type)
        if self.pagination_type == "next_page":
            self.next_page_key = config.get("next_page_key", next_page_key)
            self.next_page_key = None if self.next_page_key == [''] else self.next_page_key
        elif self.pagination_type in ["offset", "page"]:
            self.skip_key = config.get("skip_key", skip_key)

    def reset_paging(self, counting_key=None, url=None):
        self.remaining_records = 0
        self.records_to_skip = 0
        self.counting_key = counting_key
        self.counter = 0
        self.next_page_number = 0
        self.next_page_url = url
        self.is_last_batch_empty = False
        self.is_first_batch = True
        self.is_paging_started = True

    def set_counting_key(self, counting_key):
        self.counting_key = counting_key

    def update_next_page(self, data):
        self.is_first_batch = False
        self.next_page_number = self.next_page_number + 1
        if isinstance(data, list):
            batch_size = len(data)
            self.records_to_skip = self.records_to_skip + batch_size
            if batch_size == 0:
                self.is_last_batch_empty = True
            return
        elif self.counting_key:
            batch_size = len(data.get(self.counting_key, []))
            if batch_size == 0:
                self.is_last_batch_empty = True
        else:
            batch_size = 1
        if self.next_page_key and (len(self.next_page_key) > 1):
            self.next_page_url = self.get_from_path(data, self.next_page_key)
        if self.skip_key:
            self.skip = data.get(self.skip_key)
        if self.limit_key:
            self.limit = data.get(self.limit_key)
        if self.total_key:
            self.total = data.get(self.total_key)
        self.records_to_skip = self.records_to_skip + batch_size
        if self.total:
            self.remaining_records = self.total - self.records_to_skip

    def get_from_path(self, dictionary, path):
        if isinstance(path, list):
            edge = dictionary
            for key in path:
                edge = edge.get(key)
                if edge is None:
                    return None
            return edge
        else:
            return dictionary.get(path)

    def has_next_page(self):
        if self.is_last_batch_empty:
            logger.info("has_next_page:last was batch empty -> False")
            return False
        if self.is_first_batch:
            logger.info("has_next_page:is first batch -> True")
            return True
        else:
            if not self.next_page_key and not self.skip_key:
                logger.info("has_next_page:no key for next page nor skip -> False")
                return False
            if self.next_page_key and not self.next_page_url:
                logger.info("has_next_page:no next_page_url -> False")
                return False

        if self.counter == 0:
            logger.info("has_next_page:counter = 0 -> True")
            return True
        if self.next_page_key:
            ret = (self.next_page_url is not None) and (self.next_page_url != "")
            logger.info("has_next_page:next_page_key={} next_page_url={} -> {}".format(
                self.next_page_key,
                self.next_page_url,
                ret
            ))
        else:
            ret = self.counter < self.remaining_records
            logger.info("has_next_page:counter={},  remaining_records={} -> {}".format(
                self.counter,
                self.remaining_records,
                ret
            ))
        return ret

    def get_params(self):
        ret = {}
        if self.skip_key and (self.records_to_skip > 0 or self.next_page_number > 0):
            ret.update({
                self.skip_key: self.next_page_number if self.pagination_type == "page" else self.records_to_skip
            })
        return ret

    def get_next_page_url(self):
        return self.next_page_url
