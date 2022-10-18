from safe_logger import SafeLogger
from dku_utils import get_value_from_path, extract_key_using_json_path


logger = SafeLogger("api-connect plugin Pagination")


class Pagination(object):

    def __init__(self, config=None, skip_key=None, limit_key=None, total_key=None, next_page_key=None):
        self.next_page_key = None
        self.next_page_url_base = None
        self.skip_key = None
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
        self.params_must_be_blanked = False
        self.data_is_list = None
        self.update_next_page = self.update_next_page_default

    def configure_paging(self, config=None, skip_key=None, limit_key=None, total_key=None, next_page_key=None, next_page_url_base=None, url=None, pagination_type="na"):
        config = {} if config is None else config
        self.pagination_type = config.get("pagination_type", pagination_type)
        if self.pagination_type == "next_page":
            self.next_page_key = config.get("next_page_key", next_page_key)
            self.next_page_key = None if self.next_page_key == '' else self.next_page_key
            if next_page_url_base:
                next_page_url_base = next_page_url_base.strip('/')
            self.next_page_url_base = next_page_url_base
        elif self.pagination_type in ["offset", "page"]:
            self.skip_key = config.get("skip_key", skip_key)
        logger.info("configure_paging: self.pagination_type='{}', self.next_page_key='{}', self.next_page_url_base='{}', self.skip_key='{}'".format(
                self.pagination_type, self.next_page_key, self.next_page_url_base, self.skip_key
            ))
        if self.pagination_type == "next_page":
            self.update_next_page = self.update_next_page_link
        elif self.pagination_type == "offset":
            self.update_next_page = self.update_next_page_offset
        elif self.pagination_type == "page":
            self.update_next_page = self.update_next_page_per_page
        else:
            self.update_next_page = self.update_next_page_default

    def reset_paging(self, counting_key=None, url=None):
        self.remaining_records = 0
        self.records_to_skip = 0
        self.counting_key = counting_key
        self.counter = 0
        if self.pagination_type == "page":
            self.next_page_number = 1
        else:
            self.next_page_number = 0
        self.next_page_url = url
        self.is_last_batch_empty = False
        self.is_first_batch = True
        self.is_paging_started = True
        logger.info("reset_paging:next_page_url={}, counting_key={}, next_page_number={}".format(self.next_page_url, self.counting_key, self.next_page_number))

    def set_counting_key(self, counting_key):
        self.counting_key = counting_key
        logger.info("set_counting_key: counting_key set to {}".format(self.counting_key))

    def update_next_page_offset(self, data, response_links=None):
        self.is_first_batch = False
        self.counter += 1
        self.next_page_number = self.next_page_number + 1
        self.data_is_list = False
        if isinstance(data, list):
            self.data_is_list = True
            batch_size = len(data)
            self.records_to_skip = self.records_to_skip + batch_size
            if batch_size == 0:
                self.is_last_batch_empty = True
            logger.info("update_next_page:update_next_page:data is list:batch_size={}, records_to_skip={}, is_last_batch_empty={}".format(
                batch_size, self.records_to_skip, self.is_last_batch_empty
            ))
            return
        elif self.counting_key:
            extracted_data = get_value_from_path(data, self.counting_key.split("."), can_raise=False)
            if extracted_data:
                batch_size = len(extracted_data)
            else:
                batch_size = 0
                self.is_last_batch_empty = True
        else:
            batch_size = 1
        if self.skip_key:
            self.skip = data.get(self.skip_key)
            logger.info("update_next_page:skip=data[{}]={}".format(self.skip_key, self.skip))
        self.records_to_skip = self.records_to_skip + batch_size
        logger.info("update_next_page:records_to_skip={}, batch_size={}".format(self.records_to_skip, batch_size))


    def update_next_page_per_page(self, data, response_links=None):
        self.is_first_batch = False
        self.counter += 1
        self.next_page_number = self.next_page_number + 1
        self.data_is_list = False
        if isinstance(data, list):
            self.data_is_list = True
            batch_size = len(data)
            self.records_to_skip = self.records_to_skip + batch_size
            if batch_size == 0:
                self.is_last_batch_empty = True
            logger.info("update_next_page:update_next_page:data is list:batch_size={}, records_to_skip={}, is_last_batch_empty={}".format(
                batch_size, self.records_to_skip, self.is_last_batch_empty
            ))
            return
        elif self.counting_key:
            extracted_data = get_value_from_path(data, self.counting_key.split("."), can_raise=False)
            if extracted_data:
                batch_size = len(extracted_data)
            else:
                batch_size = 0
                self.is_last_batch_empty = True
        else:
            batch_size = 1
        if self.skip_key:
            self.skip = data.get(self.skip_key)
            logger.info("update_next_page:skip=data[{}]={}".format(self.skip_key, self.skip))
        self.records_to_skip = self.records_to_skip + batch_size
        logger.info("update_next_page:records_to_skip={}, batch_size={}".format(self.records_to_skip, batch_size))


    def update_next_page_link(self, data, response_links=None):
        response_links = response_links or {}
        next_link = response_links.get('next', {})
        next_page_url = next_link.get("url")
        self.is_first_batch = False
        self.counter += 1
        # self.next_page_number = self.next_page_number + 1
        if next_page_url:
            self.next_page_url = next_page_url
            self.params_must_be_blanked = True
        logger.info("update_next_page:next_link={}, next_page_url={}, params_must_be_blanked={}, next_page_number={}, counter={}".format(
            next_link, self.next_page_url, self.params_must_be_blanked, self.next_page_number, self.counter
        ))
        self.data_is_list = False
        if self.next_page_key:
            next_page_path = extract_key_using_json_path(data, self.next_page_key)
            if self.next_page_url_base and next_page_path:
                self.next_page_url = "/".join([self.next_page_url_base, next_page_path])
            else:
                self.next_page_url = next_page_path
            logger.info("update_next_page:next_page_url_base={}, next_page_path={}, next_page_url={}".format(
                self.next_page_url_base, next_page_path, self.next_page_url
            ))

    def update_next_page_default(self, data, response_links=None):
        self.is_first_batch = False
        self.counter += 1
        self.next_page_number = self.next_page_number + 1

    def has_next_page(self):
        if self.is_last_batch_empty:
            logger.info("has_next_page:last was batch empty -> False")
            return False
        if self.is_first_batch:
            logger.info("has_next_page:is first batch -> True")
            return True
        if self.pagination_type == "next_page":
            ret = (self.next_page_url is not None) and (self.next_page_url != "")
            logger.info("has_next_page:next_page_key={} next_page_url={} -> {}".format(
                self.next_page_key,
                self.next_page_url,
                ret
            ))
            return ret
        if self.pagination_type in ["page", "offset"]:
            if self.counting_key:
                #  There is a counting key and we already know the last batch was not empty
                logger.info("has_next_page:pagination_type={}, counting_key={} -> True".format(self.pagination_type, self.counting_key))
                return True
            else:
                if self.data_is_list:
                    # for lists is_last_batch_empty is set correctly and handled by the code above
                    logger.info("has_next_page:pagination_type={}, data_is_list={} -> True".format(self.pagination_type, self.data_is_list))
                    return True
                # Without a counting_key we have no mean to know if the last batch was empty.
                # To avoid infinite loop we stop pagination here
                logger.info("has_next_page:pagination_type={} -> False".format(self.pagination_type))
                return False
        logger.info("has_next_page:pagination_type={} -> False".format(self.pagination_type))
        return False

    def get_params(self):
        ret = {}
        if self.skip_key and (self.records_to_skip > 0 or self.next_page_number > 0):
            ret.update({
                self.skip_key: self.next_page_number if self.pagination_type == "page" else self.records_to_skip
            })
        return ret

    def get_next_page_url(self):
        return self.next_page_url
