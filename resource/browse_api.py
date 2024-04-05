from dss_selector_choices import DSSSelectorChoices
from rest_api_client import RestAPIClient
from dku_utils import (
    get_dku_key_values, get_endpoint_parameters,
    parse_keys_for_json, get_value_from_path, get_secure_credentials, decode_csv_data
)
import json


def get_client_from_config(config):
    endpoint_parameters = get_endpoint_parameters(config)
    secure_credentials = get_secure_credentials(config)
    credential = config.get("credential", {})
    custom_key_values = get_dku_key_values(config.get("custom_key_values", {}))
    client = RestAPIClient(credential, secure_credentials, endpoint_parameters, custom_key_values)
    return client


def do(payload, config, plugin_config, inputs):
    parameter_name = payload.get('parameterName')
    print("ALX:parameter_name={}, config={}".format(parameter_name, config))
    print("ALX:payload={}, plugin_config={}, inputs={}".format(payload, plugin_config, inputs))
    hash_key = config.get("$$hashKey")
    root_model = payload.get("rootModel", {})
    test_object = root_model.get("test_object", [])
    choices = DSSSelectorChoices()

    if parameter_name=="sub_select":
        client = get_client_from_config(config)
        choices.append("Blaa", "bla")
        choices.append("Bluu", "blu")
    if parameter_name == "extraction_path_selector":
        client = get_client_from_config(config)
        if client.has_more_data():
            try:
                json_response = client.paginated_api_call()
            except Exception as error:
                choices.append_manual_select()
                return choices.to_dss()
            likely_paths = dig_to_list(json_response)
            for likely_path in likely_paths:
                number_of_records = likely_paths.get(likely_path)
                choices.append("{} ({})".format(likely_path, number_of_records), likely_path)
        if config.get("extraction_key"):
            # Handling old flows with extraction_key already set
            choices.append_default_manual_select()
        else:
            choices.append_manual_select()
    if parameter_name=="pagination_type":
        client = get_client_from_config(config)
        if client.has_more_data():
            response = client.paginated_api_call(return_raw_response=True)
            pagination_parameters = guess_pagination_parameters(client, response)
            if pagination_parameters:
                choices.append(
                    "🤖 Auto guessing ({})".format(pagination_parameters.get("pagination_description")),
                    pagination_parameters
                )
        choices.append("No pagination", "na")
        choices.append("Next page URL provided", "next_page")
        choices.append("Offset pagination", "offset")
        choices.append("Per page", "page")
        # https://dku-qa-osi.francecentral.cloudapp.azure.com/piwebapi/assetdatabases/F1RD3VEt1yTvt0ip6-a5yeEVsgbMcrwu_Je0qg9btcZIvPswT1NJU09GVC1QSS1TRVJWXFdFTEw/elements?maxCount=1
        # https://api.2xs.in/api/dku-qa/pagination/offset/comments
        # https://services.odata.org/V3/Northwind/Northwind.svc/Order_Details?apikey=1234&$format=json
    return choices.to_dss()


def dig_to_list(json, path_to_here=None):
    path_to_here = path_to_here or "$"
    if isinstance(json, list):
        return {path_to_here:  len(json)}
    if isinstance(json, dict):
        results = {}
        for key in json:
            sub_section = json.get(key)
            results.update(dig_to_list(sub_section, path_to_here=(path_to_here + "." + key)))
        return results
    if isinstance(json, str):
        if json.strip(" ").startswith("<"):
            return {path_to_here: len(json)}
    return {}


def guess_pagination_parameters(client, response):
    pagination_parameters = {}
    headers = response.headers
    if "Link" in headers:
        link_header = headers.get("Link")
        if "next" in link_header:
            pagination_parameters["pagination_type"] = "next_page"
            pagination_parameters["pagination_description"] = "RFC"
            pagination_parameters["is_next_page_url_relative"] = "http" not in link_header
        return pagination_parameters
    json_reponse = client.get_json_from_response(response)
    path_to_link, link = scan_for_links(json_reponse)
    if path_to_link:
        pagination_parameters["pagination_type"] = "next_page"
        pagination_parameters["pagination_description"] = "Next page on '{}'".format(path_to_link)
        pagination_parameters["next_page_url_key"] = path_to_link
        pagination_parameters["is_next_page_url_relative"] = not link.startswith("http")
    return pagination_parameters


def scan_for_links(json_response):
    scan_paths = [
        ["links", "next"],
        ["_links", "next"],
        ["page", "next"],
        ["paging", "next"],
        ["next"],
        ["odata.nextLink"],
        ["meta", "pagination", "links", "next"]
    ]
    for scan_path_elements in scan_paths:
        case_corrected_path, link = path_leads_to_link(scan_path_elements, json_response)
        if link:
            return ".".join(case_corrected_path), link
    return None, None


def path_leads_to_link(scan_path_elements, json_response):
    sub_section = json_response
    case_corrected_scan_path_elements = []
    for scan_path_element in scan_path_elements:
        found_key = case_insensitive_key_search(scan_path_element, sub_section)
        sub_section = sub_section.get(found_key)
        if sub_section is None:
            return None, None
        case_corrected_scan_path_elements.append(found_key)
    return case_corrected_scan_path_elements, sub_section

def case_insensitive_key_search(searched_key, json):
    searched_key = searched_key.lower()
    for key in json:
        if key.lower() == searched_key:
            return key
