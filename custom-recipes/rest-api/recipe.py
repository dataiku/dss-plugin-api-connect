# -*- coding: utf-8 -*-
import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_recipe_config, get_output_names_for_role
from dataikuapi.utils import DataikuException
from rest_api_client import RestAPIClient
import pandas as pd
import copy
from safe_logger import SafeLogger

logger = SafeLogger("rest-api plugin", forbiden_keys=["token", "password"])


input_A_names = get_input_names_for_role('input_A_role')
config = get_recipe_config()
logger.info("config={}".format(logger.filter_secrets(config)))

credential = config.get("credential", {})
endpoint = config.get("endpoint", {})
extraction_key = endpoint.get("extraction_key", None)

id_list = dataiku.Dataset(input_A_names[0])
id_list_df = id_list.get_dataframe()
results = []
time_last_request = None

for row in id_list_df.itertuples():
    updated_endpoint = copy.deepcopy(endpoint)
    for key, value in row._asdict().items():
        updated_endpoint.update({key: value})
    logger.info("Creating client with credential={}, updated_endpoint={}".format(logger.filter_secrets(credential), updated_endpoint))
    client = RestAPIClient(credential, updated_endpoint)
    client.time_last_request = time_last_request
    client.start_paging()
    while client.has_more_data():
        json_response = client.paginated_get(can_raise_exeption=False)
        if extraction_key is None:
            base = row._asdict()
            # Todo: check api_response key is free and add something overwise
            base.update({"api_response": json_response})
            results.append(base)
        else:
            data = json_response.get(extraction_key, [json_response])
            if data is None:
                raise DataikuException("Extraction key '{}' was not found in the incoming data".format(extraction_key))
            for result in data:
                results.append(result)
    time_last_request = client.time_last_request

output_names_stats = get_output_names_for_role('api_output')
odf = pd.DataFrame(results)

if odf.size > 0:
    api_output = dataiku.Dataset(output_names_stats[0])
    api_output.write_with_schema(odf)
