import requests
import time
from pagination import Pagination
from safe_logger import SafeLogger

logger = SafeLogger("rest-api plugin", forbiden_keys=["token", "password"])


class RestAPIClient(object):

    def __init__(self, credential, endpoint):
        logger.info("Initialising RestAPIClient, credential={}, endpoint={}".format(logger.filter_secrets(credential), endpoint))
        self.presets_variables = {}
        self.presets_variables.update(endpoint)
        self.presets_variables.update(credential)

        self.requests_args = {}

        self.endpoint_query_string = endpoint.get("endpoint_query_string", "")
        user_defined_keys = credential.get("user_defined_keys", [])
        self.user_defined_keys = self.get_params(user_defined_keys, self.presets_variables)
        self.presets_variables.update(self.user_defined_keys)

        endpoint_url = endpoint.get("endpoint_url", "")
        self.endpoint_url = self.format_template(endpoint_url, **self.presets_variables)

        endpoint_headers = endpoint.get("endpoint_headers", "")
        self.endpoint_headers = self.get_params(endpoint_headers, self.presets_variables)
        self.requests_args.update({"headers": self.endpoint_headers})

        login_type = credential.get("login_type", "basic_login")
        self.extraction_key = endpoint.get("extraction_key", None)
        if login_type == "basic_login":
            self.username = credential.get("username", "")
            self.password = credential.get("password", "")
            self.auth = (self.username, self.password)
            self.requests_args.update({"auth": self.auth})
        if login_type == "token":
            self.token = credential.get("token", "")
        self.params = self.get_params(self.endpoint_query_string, self.presets_variables)
        self.ignore_ssl_check = endpoint.get("ignore_ssl_check", False)
        if self.ignore_ssl_check:
            self.requests_args.update({"verify": False})
        else:
            self.requests_args.update({"verify": True})
        self.timeout = endpoint.get("timeout", -1)
        if self.timeout > 0:
            self.requests_args.update({"timeout": self.timeout})

        self.requests_args.update({"params": self.params})
        self.pagination = Pagination()
        next_page_url_key = endpoint.get("next_page_url_key", "").split(',')
        top_key = endpoint.get("top_key")
        skip_key = endpoint.get("skip_key")
        self.pagination.configure_paging(skip_key=skip_key, limit_key=top_key, next_page_key=next_page_url_key, url=self.endpoint_url)
        self.last_interaction = None
        self.requests_per_minute = endpoint.get("requests_per_minute", -1)
        if self.requests_per_minute > 0:
            self.time_between_requests = 60 / self.requests_per_minute
        else:
            self.time_between_requests = None
        self.time_last_request = None

    def get(self, url, can_raise_exeption=True, **kwargs):
        logger.info("Accessing endpoint {}".format(url))
        self.enforce_throttling()
        response = requests.get(url, **kwargs)
        self.time_last_request = time.time()
        if response.status_code >= 400:
            error_message = "Error {}: {}".format(response.status_code, response.content)
            self.pagination.is_last_batch_empty = True
            if can_raise_exeption:
                raise Exception(error_message)
            else:
                return {"error": error_message}
        json_response = response.json()
        self.pagination.update_next_page(json_response)
        return json_response

    def paginated_get(self, can_raise_exeption=True, **kwargs):
        pagination_params = self.pagination.get_params()
        params = self.requests_args.get("params")
        params.update(pagination_params)
        self.requests_args.update({"params": params})
        return self.get(self.pagination.get_next_page_url(), can_raise_exeption, **self.requests_args)

    def get_params(self, endpoint_query_string, keywords):
        ret = {}
        for key_value in endpoint_query_string:
            key = key_value.get("from")
            value = key_value.get("to")
            ret.update({key: self.format_template(value, **keywords)})
        return ret

    def format_template(self, template, **kwargs):
        try:
            template = template.format(**kwargs)
        except KeyError as key:  # This has to go
            logger.error('Key {} not found for template "{}"'.format(key, template))
        return template

    def has_more_data(self):
        return self.pagination.is_next_page()

    def start_paging(self):
        self.pagination.reset_paging(counting_key=self.extraction_key, url=self.endpoint_url)

    def enforce_throttling(self):
        if self.time_between_requests and self.time_last_request:
            current_time = time.time()
            time_since_last_resquests = current_time - self.time_last_request
            if time_since_last_resquests < self.time_between_requests:
                logger.info("Enforcing {}s throttling".format(self.time_between_requests - time_since_last_resquests))
                time.sleep(self.time_between_requests - time_since_last_resquests)
