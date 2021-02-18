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
dku_flow_variables = dataiku.get_flow_variables()

logger.info("config={}".format(logger.filter_secrets(config)))

credential_parameters = config.get("credential", {})
endpoint_parameters = config.get("endpoint", {})
extraction_key = endpoint_parameters.get("extraction_key", "")
raw_output = endpoint_parameters.get("raw_output", None)
parameter_columns = config.get("parameter_columns", [])
if len(parameter_columns) == 0:
    raise ValueError("There is no parameter column selected.")
parameter_renamings = get_dku_key_values(config.get("parameter_renamings", {}))

column_to_parameter_dict = {}
for parameter_column in parameter_columns:
    if parameter_column in parameter_renamings:
        column_to_parameter_dict[parameter_column] = parameter_renamings[parameter_column]
    else:
        column_to_parameter_dict[parameter_column] = parameter_column
custom_key_values = get_dku_key_values(config.get("custom_key_values", {}))
id_list = dataiku.Dataset(input_A_names[0])
partitioning = id_list.get_config().get("partitioning")
if partitioning:
    dimensions_types = partitioning.get("dimensions", [])
    dimensions = []
    for dimension_type in dimensions_types:
        dimensions.append(dimension_type.get("name"))
    for dimension in dimensions:
        dimension_src = "DKU_DST_{}".format(dimension)
        if dimension_src in dku_flow_variables:
            custom_key_values[dimension] = dku_flow_variables.get(dimension_src)
id_list_df = id_list.get_dataframe()
results = []
time_last_request = None

for index, input_row in id_list_df.iterrows():
    updated_endpoint_parameters = copy.deepcopy(endpoint_parameters)
    initial_parameter_columns = {}
    if column_to_parameter_dict == {}:
        for key, value in input_row._asdict().items():
            updated_endpoint_parameters.update({key: value})
    else:
        for column_name in column_to_parameter_dict:
            parameter_name = column_to_parameter_dict[column_name]
            updated_endpoint_parameters.update({parameter_name: input_row[column_name]})
            initial_parameter_columns.update({parameter_name: input_row[column_name]})
    logger.info("Creating client with credential={}, updated_endpoint={}, custom_key_values={}".format(
        logger.filter_secrets(credential_parameters),
        updated_endpoint_parameters,
        custom_key_values
    ))
    client = RestAPIClient(credential_parameters, updated_endpoint_parameters, custom_key_values=custom_key_values)
    client.time_last_request = time_last_request
    while client.has_more_data():
        base_row = copy.deepcopy(initial_parameter_columns)
        json_response = client.paginated_get(can_raise_exeption=False)
        if extraction_key:
            data_rows = json_response.get(extraction_key, [json_response])
            if data_rows is None:
                raise DataikuException("Extraction key '{}' was not found in the incoming data".format(extraction_key))
            for data_row in data_rows:
                base_row = copy.deepcopy(initial_parameter_columns)
                if raw_output:
                    if is_error_message(data_row):
                        base_row.update(data_row)
                    else:
                        base_row.update({"api_response": data_row})
                else:
                    base_row.update(data_row)
                results.append(base_row)
        else:
            # Todo: check api_response key is free and add something overwise
            if is_error_message(json_response):
                base_row.update(json_response)
            else:
                base_row.update({"api_response": json_response})
            results.append(base_row)
    time_last_request = client.time_last_request

output_names_stats = get_output_names_for_role('api_output')
odf = pd.DataFrame(results)

if odf.size > 0:
    api_output = dataiku.Dataset(output_names_stats[0])
    api_output.write_with_schema(odf)
