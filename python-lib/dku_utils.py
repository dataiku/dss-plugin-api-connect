import json
import copy
import math
from collections import defaultdict
from jsonpath_ng.ext import parse
from safe_logger import SafeLogger


logger = SafeLogger("api-connect plugin utils")


def get_dku_key_values(endpoint_query_string):
    result = defaultdict(list)
    for kv in endpoint_query_string:
        if kv.get('from') and kv.get('to'):
            result[kv['from'].strip()].append(kv['to'].strip())
    return dict(result)



def get_endpoint_parameters(configuration):
    endpoint_parameters = [
        "endpoint_url",
        "http_method",
        "endpoint_query_string",
        "endpoint_body",
        "endpoint_headers",
        "body_format",
        "text_body",
        "key_value_body",
        "extraction_key",
        "raw_output",
        "ignore_ssl_check",
        "redirect_auth_header",
        "timeout",
        "requests_per_minute",
        "pagination_type",
        "next_page_url_key", "is_next_page_url_relative", "next_page_url_base",
        "top_key", "skip_key", "maximum_number_rows"
    ]
    parameters = {
        endpoint_parameter: configuration.get(endpoint_parameter) for endpoint_parameter in endpoint_parameters if configuration.get(endpoint_parameter) is not None
    }
    return parameters


def get_secure_credentials(configuration):
    secure_credentials = {}
    auth_type = configuration.get("auth_type")
    if auth_type:
        secure_credentials["auth_type"] = auth_type
    if auth_type == "secure_basic":
        secure_credentials["login_type"] = configuration.get("login_type")
        secure_basic = configuration.get("secure_basic", {})
        secure_token = secure_basic.pop("secure_token", {})
        secure_credentials.update(secure_basic)
        secure_credentials.update(secure_token)

    if auth_type == "secure_oauth":
        secure_credentials["login_type"] = "bearer_token"
        secure_oauth = configuration.get("secure_oauth", {})
        secure_credentials["token"] = secure_oauth.pop("secure_token")
        secure_credentials.update(secure_oauth)
    return secure_credentials


def parse_keys_for_json(items):
    ret = {}
    for key in items:
        value = items.get(key)
        if isinstance(value, dict) or isinstance(value, list):
            ret.update({key: json.dumps(value)})
        elif value is None:
            continue
        else:
            ret.update({key: value})
    return ret


def get_value_from_path(dictionary, path, default=None, can_raise=True):
    ret = copy.deepcopy(dictionary)
    for key in path:
        if isinstance(ret, dict) and (key in ret):
            ret = ret.get(key)
        else:
            error_message = "The extraction path {} was not found in the incoming data".format(path)
            if can_raise:
                raise ValueError(error_message)
            elif default:
                return default  # [{"error": error_message}]
            else:
                return None
    return ret


def template_dict(dictionnary, **kwargs):
    """ Recurses into dictionnary and replace template {{keys}} with the matching values present in the kwargs dictionnary"""
    ret = dict.copy(dictionnary)
    for key in ret:
        if isinstance(ret[key], dict):
            ret[key] = template_dict(ret[key], **kwargs)
        if is_string(ret[key]):
            ret[key] = format_template(ret[key], **kwargs)
    return ret


def format_template(template, allow_list=False, **kwargs):
    """
    Replace {{key}} in template with the value(s) in the kwargs dictionnary.
    If allow_list is False, list inputs will be joined into a comma-separated string (for headers).
    If allow_list is True, lists will be returned as lists (for query params).
    """
    def replace_in(template):
        formated = template
        for key, value in kwargs.items():
            formated = formated.replace(f"{{{{{key}}}}}", str(value))
        return formated
    if template is None:
        return None
    elif isinstance(template, list):
        replaced_list = [replace_in(item) for item in template]
        if allow_list:
            return replaced_list
        else:
            # To handle headers
            return ", ".join(replaced_list)
    elif isinstance(template, str):
        return replace_in(template)
    else:
        return template


def is_string(data):
    data_type = type(data).__name__
    return data_type in ["str", "unicode"]


def extract_key_using_json_path(json_dictionary, json_path):
    matches = parse(json_path).find(json_dictionary)
    if matches:
        res = matches[0].value
        return res
    else:
        return None


def is_reponse_xml(response):
    content_types = response.headers.get("Content-Type", "").split(";")
    for content_type in content_types:
        if content_type in ["text/xml", "application/soap+xml", "application/xml", "application/atom+xml"]:
            return True
    return False


def xml_to_json(content):
    import xmltodict
    json_response = None
    try:
        json_response = xmltodict.parse(content)
    except Exception as error:
        logger.error("XML to JSON conversion failed, processing as STRING ({})".format(error))
        json_response = content
    return json_response


def decode_csv_data(data):
    import csv
    import io
    json_data = None
    data = decode_bytes(data)
    try:
        reader = csv.DictReader(io.StringIO(data))
        json_data = list(reader)
    except Exception as error:
        logger.error("Could not extract csv data. Error={}".format(error))
        json_data = data
    return json_data


def de_NaN(cell_content):
    if isinstance(cell_content, float):
        if math.isnan(cell_content):
            return ''
    return cell_content


def decode_bytes(content):
    if isinstance(content, bytes):
        content = content.decode()
    return content
