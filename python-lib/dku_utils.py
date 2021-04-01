def get_dku_key_values(endpoint_query_string):
    return {key_value.get("from"): key_value.get("to") for key_value in endpoint_query_string if key_value.get("from")}


def get_endpoint_presets(configuration):
    endpoint_presets = [
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
    presets = {endpoint_preset: configuration.get(endpoint_preset) for endpoint_preset in endpoint_presets if configuration.get(endpoint_preset) is not None}
    return presets
