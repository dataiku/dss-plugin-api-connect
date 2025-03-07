# -*- coding: utf-8 -*-
import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_recipe_config, get_output_names_for_role
import pandas as pd
from safe_logger import SafeLogger
from dku_utils import get_dku_key_values, get_endpoint_parameters, get_secure_credentials, get_user_secrets
from rest_api_recipe_session import RestApiRecipeSession
from dku_constants import DKUConstants


logger = SafeLogger("api-connect plugin", forbidden_keys=DKUConstants.FORBIDDEN_KEYS)


def get_partitioning_keys(id_list, dku_flow_variables):
    partitioning_keys = {}
    partitioning = id_list.get_config().get("partitioning")
    if partitioning:
        dimensions_types = partitioning.get("dimensions", [])
        dimensions = []
        for dimension_type in dimensions_types:
            dimensions.append(dimension_type.get("name"))
        for dimension in dimensions:
            dimension_src = "DKU_DST_{}".format(dimension)
            if dimension_src in dku_flow_variables:
                partitioning_keys[dimension] = dku_flow_variables.get(dimension_src)
    return partitioning_keys


logger.info('API-Connect plugin recipe v{}'.format(DKUConstants.PLUGIN_VERSION))

input_A_names = get_input_names_for_role('input_A_role')
config = get_recipe_config()
dku_flow_variables = dataiku.get_flow_variables()

logger.info("config={}".format(logger.filter_secrets(config)))

credential_parameters = config.get("credential", {})
behaviour_when_error = config.get("behaviour_when_error", "add-error-column")
endpoint_parameters = get_endpoint_parameters(config)
secure_credentials = get_secure_credentials(config)
extraction_key = endpoint_parameters.get("extraction_key", "")
is_raw_output = endpoint_parameters.get("raw_output", True)
parameter_columns = [column for column in config.get("parameter_columns", []) if column]
if len(parameter_columns) == 0:
    raise ValueError("There is no parameter column selected.")
parameter_renamings = get_dku_key_values(config.get("parameter_renamings", {}))
custom_key_values = get_dku_key_values(config.get("custom_key_values", {}))
user_secrets = get_user_secrets(config)
custom_key_values.update(user_secrets)
display_metadata = config.get("display_metadata", False)
maximum_number_rows = config.get("maximum_number_rows", -1)
input_parameters_dataset = dataiku.Dataset(input_A_names[0])
partitioning_keys = get_partitioning_keys(input_parameters_dataset, dku_flow_variables)
custom_key_values.update(partitioning_keys)
input_parameters_dataframe = input_parameters_dataset.get_dataframe()

recipe_session = RestApiRecipeSession(
    custom_key_values,
    credential_parameters,
    secure_credentials,
    endpoint_parameters,
    extraction_key,
    parameter_columns,
    parameter_renamings,
    display_metadata,
    maximum_number_rows=maximum_number_rows,
    behaviour_when_error=behaviour_when_error
)
results = recipe_session.process_dataframe(input_parameters_dataframe, is_raw_output)

output_names_stats = get_output_names_for_role('api_output')
odf = pd.DataFrame(results)

if odf.size > 0:
    api_output = dataiku.Dataset(output_names_stats[0])
    api_output.write_with_schema(odf)
