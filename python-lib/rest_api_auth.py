import requests
import logging
import urllib.parse


logging.basicConfig(level=logging.INFO, format='dss-plugin-api-connect %(levelname)s - %(message)s')
logger = logging.getLogger()


class RestApiAuth(requests.auth.AuthBase):
    def __init__(self, credential):
        self.credential = credential
        self.login_type = credential.get("login_type", "no_auth")
        self.api_key_destination = None
        self.auth_key = None
        self.access_token_getter = None
        if self.login_type == "bearer_token":
            token = credential.get("token", "")
            bearer_template = credential.get("bearer_template", "Bearer {{token}}")
            bearer_template = bearer_template.replace("{{token}}", token)
            self.auth_key = "Authorization"
            self.api_key_destination = "header"
        elif self.login_type == "api_key":
            self.auth_key = credential.get("api_key_name", "")
            self.api_key_destination = credential.get("api_key_destination", "header")

    def __call__(self, request):
        if self.api_key_destination == "header":
            request.headers[self.auth_key] = self._get_auth_value()
        elif self.api_key_destination == "params":
            request.url = update_query_string(request.url, {self.auth_key: self._get_auth_value()})
        return request

    def _get_auth_value(self):
        if self.login_type == "bearer_token":
            token = self._get_fresh_token()
            bearer_template = self.credential.get("bearer_template", "Bearer {{token}}")
            bearer_template = bearer_template.replace("{{token}}", token)
            self.auth_key = "Authorization"
            auth_value = bearer_template
            self.api_key_destination = "header"
        elif self.login_type == "api_key":
            auth_value = self.credential.get("api_key_value", "")
        return auth_value

    def _get_fresh_token(self):
        if self.access_token_getter is None:
            if "__credentials" in self.credential:
                logger.info("Refreshable access token")
                from dataiku.core import plugin
                self.access_token_getter = plugin.OAuthCredentials(self.credential.get("__credentials", {}).get("secure_token"))
            else:
                return self.credential.get("token", "")
        return self.access_token_getter.access_token


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
    return None


def update_query_string(old_url, request_params_to_update):
    url_parts = urllib.parse.urlparse(old_url)
    request_params = dict(urllib.parse.parse_qsl(url_parts.query))
    request_params.update(request_params_to_update)
    request_params = urllib.parse.urlencode(request_params)
    new_url = url_parts._replace(query=request_params).geturl()
    return new_url
