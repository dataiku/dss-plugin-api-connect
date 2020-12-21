# -*- coding: utf-8 -*-
import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_recipe_config, get_output_names_for_role
from dataikuapi.utils import DataikuException
from rest_api_client import RestAPIClient
import pandas as pd
import copy
from safe_logger import SafeLogger
from dku_utils import get_dku_key_values

logger = SafeLogger("rest-api plugin", forbiden_keys=["token", "password"])


def is_error_message(jsons_response):
    if "error" in jsons_response and len(jsons_response) == 1:
        return True
    else:
        return False


input_A_names = get_input_names_for_role('input_A_role')
config = get_recipe_config()
logger.info("config={}".format(logger.filter_secrets(config)))

credential = config.get("credential", {})
endpoint = config.get("endpoint", {})
extraction_key = endpoint.get("extraction_key", "")
raw_output = endpoint.get("raw_output", None)
parameter_columns = config.get("parameter_columns", [])
if len(parameter_columns) == 0:
    raise ValueError("There is no parameter column selected.")
parameter_renamings = get_dku_key_values(config.get("parameter_renamings", {}))

column_to_parameter = {}
for parameter_column in parameter_columns:
    if parameter_column in parameter_renamings:
        column_to_parameter[parameter_column] = parameter_renamings[parameter_column]
    else:
        column_to_parameter[parameter_column] = parameter_column
custom_key_values = get_dku_key_values(config.get("custom_key_values", {}))
id_list = dataiku.Dataset(input_A_names[0])
id_list_df = id_list.get_dataframe()
results = []
time_last_request = None

#for row in id_list_df.itertuples():
for index, row in id_list_df.iterrows():
    updated_endpoint = copy.deepcopy(endpoint)
    if column_to_parameter == {}:
        for key, value in row._asdict().items():
            updated_endpoint.update({key: value})
    else:
        for column_name in column_to_parameter:
            parameter_name = column_to_parameter[column_name]
            updated_endpoint.update({parameter_name: row[column_name]})
    logger.info("Creating client with credential={}, updated_endpoint={}".format(logger.filter_secrets(credential), updated_endpoint))
    client = RestAPIClient(credential, updated_endpoint, custom_key_values=custom_key_values)
    client.time_last_request = time_last_request
    #client.start_paging()
    while client.has_more_data():
        json_response = client.paginated_get(can_raise_exeption=False)
        print("ALX:extraction_key={}".format(extraction_key))
        if extraction_key == "":
            base = row.to_dict()
            print("ALX:base={}".format(base))
            # Todo: check api_response key is free and add something overwise
            if is_error_message(json_response):
                base.update(json_response)
            else:
                base.update({"api_response": json_response})
                print("ALX:base after={}".format(base))
            results.append(base)
        else:
            data = json_response.get(extraction_key, [json_response])
            if data is None:
                raise DataikuException("Extraction key '{}' was not found in the incoming data".format(extraction_key))
            for result in data:
                if raw_output:
                    if is_error_message(result):
                        results.append(result)
                    else:
                        results.append({"api_response": result})
                else:
                    results.append(result)
    time_last_request = client.time_last_request

output_names_stats = get_output_names_for_role('api_output')
odf = pd.DataFrame(results)

if odf.size > 0:
    api_output = dataiku.Dataset(output_names_stats[0])
    api_output.write_with_schema(odf)
