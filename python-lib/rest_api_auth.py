import requests
import logging
import urllib.parse


logging.basicConfig(level=logging.INFO, format='dss-plugin-microstrategy %(levelname)s - %(message)s')
logger = logging.getLogger()


class RestApiAuth(requests.auth.AuthBase):
    def __init__(self, credential):
        login_type = credential.get("login_type", "no_auth")
        self.api_key_destination = None
        self.auth_key = None
        self.auth_value = None
        if login_type == "bearer_token":
            token = credential.get("token", "")
            bearer_template = credential.get("bearer_template", "Bearer {{token}}")
            bearer_template = bearer_template.replace("{{token}}", token)
            self.auth_key = "Authorization"
            self.auth_value = bearer_template
            self.api_key_destination = "header"
        elif login_type == "api_key":
            self.auth_key = credential.get("api_key_name", "")
            self.auth_value = credential.get("api_key_value", "")
            self.api_key_destination = credential.get("api_key_destination", "header")
        else:
            return None

    def __call__(self, request):
        if self.api_key_destination == "header":
            request.headers[self.auth_key] = self.auth_value
        elif self.api_key_destination == "params":
            request.url = update_query_string(request.url, {self.auth_key:self.auth_value})
        return request


def get_auth(credential):
    login_type = credential.get("login_type", "no_auth")
    if login_type == "basic_login":
        username = credential.get("username", credential.get("user", ""))
        password = credential.get("password", "")
        return (username, password)
    if login_type == "ntlm":
        from requests_ntlm import HttpNtlmAuth
        username = credential.get("username", credential.get("user", ""))
        password = credential.get("password", "")
        return HttpNtlmAuth(username, password)
    if login_type in ["bearer_token", "api_key"]:
        return RestApiAuth(credential)


def update_query_string(old_url, request_params_to_update):
    url_parts = urllib.parse.urlparse(old_url)
    request_params = dict(urllib.parse.parse_qsl(url_parts.query))
    request_params.update(request_params_to_update)
    request_params=urllib.parse.urlencode(request_params)
    new_url = url_parts._replace(query=request_params).geturl()
    return new_url
