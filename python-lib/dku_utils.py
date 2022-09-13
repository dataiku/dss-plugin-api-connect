import json
import copy
from jsonpath_ng.ext import parse


def get_dku_key_values(endpoint_query_string):
    return {key_value.get("from"): key_value.get("to") for key_value in endpoint_query_string if key_value.get("from")}


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
        "next_page_url_key",
        "top_key", "skip_key", "maximum_number_rows"
    ]
    parameters = {endpoint_parameter: configuration.get(endpoint_parameter) for endpoint_parameter in endpoint_parameters if configuration.get(endpoint_parameter) is not None}
    return parameters


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
        if key in ret and isinstance(ret, dict):
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


def format_template(template, **kwargs):
    """ Replace {{keys}} elements in template with the matching value in the kwargs dictionnary"""
    if template is None:
        return None
    formated = template
    for key in kwargs:
        replacement = kwargs.get(key, "")
        formated = formated.replace("{{{{{}}}}}".format(key), str(replacement))
    return formated


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
