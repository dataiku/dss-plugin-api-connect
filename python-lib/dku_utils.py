def get_dku_key_values(endpoint_query_string):
    ret = {}
    for key_value in endpoint_query_string:
        key = key_value.get("from")
        value = key_value.get("to")
        ret.update({key: value})
    return ret
