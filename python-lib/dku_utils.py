def get_dku_key_values(endpoint_query_string):
    return {key_value.get("from"): key_value.get("to") for key_value in endpoint_query_string}
