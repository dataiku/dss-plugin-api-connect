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
        "timeout",
        "requests_per_minute",
        "pagination_type",
        "next_page_url_key",
        "top_key", "skip_key"
    ]
    parameters = {endpoint_parameter: configuration.get(endpoint_parameter) for endpoint_parameter in endpoint_parameters if configuration.get(endpoint_parameter) is not None}
    return parameters
