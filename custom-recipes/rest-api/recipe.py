# -*- coding: utf-8 -*-
import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_recipe_config, get_output_names_for_role
from rest_api_client import RestAPIClient
import pandas as pd
import copy
from safe_logger import SafeLogger

logger = SafeLogger("rest-api plugin", forbiden_keys=["token", "password"])


input_A_names = get_input_names_for_role('input_A_role')
config = get_recipe_config()
logger.info("config={}".format(logger.filter_secrets(config)))

parameter_columns = config.get("parameter_columns", [])
credential = config.get("credential", {})
endpoint = config.get("endpoint", {})
extraction_key = endpoint.get("extraction_key", None)

id_list = dataiku.Dataset(input_A_names[0])
id_list_df = id_list.get_dataframe()
results = []

for index, row in id_list_df.iterrows():
    updated_endpoint = copy.deepcopy(endpoint)
    for parameter_column in parameter_columns:
        if parameter_column is not None:
            updated_endpoint.update({parameter_column: row[parameter_column]})
    logger.info("Creating client with credential={}, updated_endpoint={}".format(logger.filter_secrets(credential), updated_endpoint))
    client = RestAPIClient(credential, updated_endpoint)
    client.start_paging()
    while client.has_more_data():
        json_response = client.paginated_get(can_raise_exeption=False)
        if extraction_key is None:
            data = json_response
        else:
            data = json_response.get(extraction_key, [json_response])
            if data is None:
                raise Exception("Extraction key '{}' was not found in the incoming data".format(self.extraction_key))
        for result in data:
            results.append(result)

output_names_stats = get_output_names_for_role('api_output')
odf = pd.DataFrame(results)

if odf.size > 0:
    api_output = dataiku.Dataset(output_names_stats[0])
    api_output.write_with_schema(odf)
