import requests
import time
import copy
from pagination import Pagination
from safe_logger import SafeLogger
from loop_detector import LoopDetector
from dku_utils import get_dku_key_values, template_dict, format_template
from dku_constants import DKUConstants


logger = SafeLogger("api-connect plugin", forbidden_keys=DKUConstants.FORBIDDEN_KEYS)


class RestAPIClientError(ValueError):
    pass


class RestAPIClient(object):

    def __init__(self, credential, endpoint, custom_key_values={}, session=None):
        logger.info("Initialising RestAPIClient, credential={}, endpoint={}".format(logger.filter_secrets(credential), endpoint))

        #  presets_variables contains all variables available in templates using the {{variable_name}} notation
        self.presets_variables = {}
        self.presets_variables.update(endpoint)
        self.presets_variables.update(credential)
        self.presets_variables.update(custom_key_values)

        #  requests_kwargs contains **kwargs used for requests
        self.requests_kwargs = {}

        self.endpoint_query_string = endpoint.get("endpoint_query_string", [])
        user_defined_keys = credential.get("user_defined_keys", [])
        self.user_defined_keys = self.get_params(user_defined_keys, self.presets_variables)
        self.presets_variables.update(self.user_defined_keys)

        endpoint_url = endpoint.get("endpoint_url", "")
        self.endpoint_url = format_template(endpoint_url, **self.presets_variables)
        self.http_method = endpoint.get("http_method", "GET")

        endpoint_headers = endpoint.get("endpoint_headers", "")
        self.endpoint_headers = self.get_params(endpoint_headers, self.presets_variables)

        self.params = self.get_params(self.endpoint_query_string, self.presets_variables)

        self.extraction_key = endpoint.get("extraction_key", None)

        self.set_login(credential)

        self.requests_kwargs.update({"headers": self.endpoint_headers})
        self.ignore_ssl_check = endpoint.get("ignore_ssl_check", False)
        if self.ignore_ssl_check:
            self.requests_kwargs.update({"verify": False})
        else:
            self.requests_kwargs.update({"verify": True})
        self.redirect_auth_header = endpoint.get("redirect_auth_header", False)
        self.timeout = endpoint.get("timeout", -1)
        if self.timeout > 0:
            self.requests_kwargs.update({"timeout": self.timeout})

        self.requests_kwargs.update({"params": self.params})
        self.pagination = Pagination()
        next_page_url_key = endpoint.get("next_page_url_key", "")
        is_next_page_url_relative = endpoint.get("is_next_page_url_relative", False)
        next_page_url_base = endpoint.get("next_page_url_base", None) if is_next_page_url_relative else None
        next_page_url_base = format_template(next_page_url_base, **self.presets_variables)
        skip_key = endpoint.get("skip_key")
        pagination_type = endpoint.get("pagination_type", "na")
        if pagination_type == "next_page" and is_next_page_url_relative and not next_page_url_base:
            raise RestAPIClientError("Pagination's 'Next page URL' is relative but no 'Base URL to next page' has been set")
        self.pagination.configure_paging(
            skip_key=skip_key,
            next_page_key=next_page_url_key,
            next_page_url_base=next_page_url_base,
            pagination_type=pagination_type
        )
        self.last_interaction = None
        self.requests_per_minute = endpoint.get("requests_per_minute", -1)
        if self.requests_per_minute > 0:
            self.time_between_requests = 60 / self.requests_per_minute
        else:
            self.time_between_requests = None
        self.time_last_request = None
        self.loop_detector = LoopDetector()
        body_format = endpoint.get("body_format", None)
        if body_format == DKUConstants.RAW_BODY_FORMAT:
            text_body = endpoint.get("text_body", "")
            self.requests_kwargs.update({"data": text_body})
        elif body_format in [DKUConstants.FORM_DATA_BODY_FORMAT]:
            key_value_body = endpoint.get("key_value_body", {})
            self.requests_kwargs.update({"json": get_dku_key_values(key_value_body)})
        self.metadata = {}
        self.call_number = 0
        self.session = session or requests.Session()

    def set_login(self, credential):
        login_type = credential.get("login_type", "no_auth")
        if login_type == "basic_login":
            username = credential.get("username", "")
            password = credential.get("password", "")
            auth = (username, password)
            self.requests_kwargs.update({"auth": auth})
        if login_type == "ntlm":
            from requests_ntlm import HttpNtlmAuth
            username = credential.get("username", "")
            password = credential.get("password", "")
            auth = HttpNtlmAuth(username, password)
            self.requests_kwargs.update({"auth": auth})
        if login_type == "bearer_token":
            token = credential.get("token", "")
            bearer_template = credential.get("bearer_template", "Bearer {{token}}")
            bearer_template = bearer_template.replace("{{token}}", token)
            self.endpoint_headers.update({"Authorization": bearer_template})
        if login_type == "api_key":
            self.api_key_name = credential.get("api_key_name", "")
            self.api_key_value = credential.get("api_key_value", "")
            self.api_key_destination = credential.get("api_key_destination", "header")
            if self.api_key_destination == "header":
                self.endpoint_headers.update({self.api_key_name: self.api_key_value})
            else:
                self.params.update({self.api_key_name: self.api_key_value})

    def get(self, url, can_raise_exeption=True, **kwargs):
        json_response = self.request("GET", url, can_raise_exeption=can_raise_exeption, **kwargs)
        return json_response

    def request(self, method, url, can_raise_exeption=True, **kwargs):
        logger.info(u"Accessing endpoint {} with params={}".format(url, kwargs.get("params")))
        self.enforce_throttling()
        kwargs = template_dict(kwargs, **self.presets_variables)
        if self.loop_detector.is_stuck_in_loop(url, kwargs.get("params", {}), kwargs.get("headers", {})):
            raise RestAPIClientError("The api-connect plugin is stuck in a loop. Please check the pagination parameters.")
        request_start_time = time.time()
        self.time_last_request = request_start_time
        error_message = None
        try:
            response = self.request_with_redirect_retry(method, url, **kwargs)
        except Exception as err:
            self.pagination.is_last_batch_empty = True
            error_message = "Error: {}".format(err)
            if can_raise_exeption:
                raise RestAPIClientError(error_message)

        request_finish_time = time.time()
        self.set_metadata("request_duration", request_finish_time - request_start_time)
        self.set_metadata("status_code", response.status_code)
        self.set_metadata("response_headers", "{}".format(response.headers))

        if error_message:
            return {"error": error_message}

        if response.status_code >= 400:
            error_message = "Error {}: {}".format(response.status_code, response.content)
            self.pagination.is_last_batch_empty = True
            if can_raise_exeption:
                raise RestAPIClientError(error_message)
            else:
                return {"error": error_message}
        if response.status_code in [204]:
            self.pagination.update_next_page({}, response.links)
            return self.empty_json_response()
        try:
            json_response = response.json()
        except Exception as err:
            self.pagination.update_next_page({}, None)
            error_message = "Error '{}' when decoding JSON".format(str(err)[:100])
            logger.error(error_message)
            logger.error("response.content={}".format(response.content))
            if can_raise_exeption:
                raise RestAPIClientError("The API did not return JSON as expected. {}".format(error_message))
            return {"error": error_message}

        self.pagination.update_next_page(json_response, response.links)
        return json_response

    def request_with_redirect_retry(self, method, url, **kwargs):
        # In case of redirection to another domain, the authorization header is not kept
        # If redirect_auth_header is true, another attempt is made with initial headers to the redirected url
        response = self.session.request(method, url, **kwargs)
        if self.redirect_auth_header and not response.url.startswith(url):
            redirection_kwargs = copy.deepcopy(kwargs)
            redirection_kwargs.pop("params", None)  # params are contained in the redirected url
            logger.warning("Redirection ! Accessing endpoint {} with initial authorization headers".format(response.url))
            response = self.session.request(method, response.url, **redirection_kwargs)
        return response

    def paginated_api_call(self, can_raise_exeption=True):
        if self.pagination.params_must_be_blanked:
            self.requests_kwargs["params"] = {}
        else:
            pagination_params = self.pagination.get_params()
            params = self.requests_kwargs.get("params")
            params.update(pagination_params)
            self.requests_kwargs.update({"params": params})
        self.call_number = self.call_number + 1
        logger.info("API call number #{}".format(self.call_number))
        return self.request(self.http_method, self.pagination.get_next_page_url(), can_raise_exeption, **self.requests_kwargs)

    def empty_json_response(self):
        return {self.extraction_key: {}} if self.extraction_key else {}

    def set_metadata(self, metadata_name, value):
        self.metadata["dku_{}".format(metadata_name)] = value

    @staticmethod
    def get_params(endpoint_query_string, keywords):
        templated_query_string = get_dku_key_values(endpoint_query_string)
        ret = {}
        for key in templated_query_string:
            ret.update({key: format_template(templated_query_string.get(key, ""), **keywords) or ""})
        return ret

    def has_more_data(self):
        if not self.pagination.is_paging_started:
            self.start_paging()
        return self.pagination.has_next_page()

    def start_paging(self):
        logger.info("Start paging with counting key '{}'".format(self.extraction_key))
        self.pagination.reset_paging(counting_key=self.extraction_key, url=self.endpoint_url)

    def enforce_throttling(self):
        if self.time_between_requests and self.time_last_request:
            current_time = time.time()
            time_since_last_resquests = current_time - self.time_last_request
            if time_since_last_resquests < self.time_between_requests:
                logger.info("Enforcing {}s throttling".format(self.time_between_requests - time_since_last_resquests))
                time.sleep(self.time_between_requests - time_since_last_resquests)

    def get_metadata(self):
        return self.metadata
