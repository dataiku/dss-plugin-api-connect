from dataikuapi.utils import DataikuException
from rest_api_client import RestAPIClient
from safe_logger import SafeLogger
from dku_utils import parse_keys_for_json, get_value_from_path
from dku_constants import DKUConstants
import copy
import json
import requests


logger = SafeLogger("api-connect plugin", forbidden_keys=DKUConstants.FORBIDDEN_KEYS)


class RestApiRecipeSession:
    def __init__(self, custom_key_values, credential_parameters, endpoint_parameters, extraction_key, parameter_columns, parameter_renamings,
                 display_metadata=False,
                 maximum_number_rows=-1, behaviour_when_error=None):
        self.custom_key_values = custom_key_values
        self.credential_parameters = credential_parameters
        self.endpoint_parameters = endpoint_parameters
        self.extraction_key = extraction_key
        self.client = None
        self.initial_parameter_columns = None
        self.column_to_parameter_dict = self.get_column_to_parameter_dict(parameter_columns, parameter_renamings)
        self.display_metadata = display_metadata
        self.maximum_number_rows = maximum_number_rows
        self.is_row_limit = (self.maximum_number_rows > 0)
        self.behaviour_when_error = behaviour_when_error or "add-error-column"
        self.can_raise = self.behaviour_when_error == "raise"

    @staticmethod
    def get_column_to_parameter_dict(parameter_columns, parameter_renamings):
        column_to_parameter_dict = {}
        for parameter_column in parameter_columns:
            if parameter_column in parameter_renamings:
                column_to_parameter_dict[parameter_column] = parameter_renamings[parameter_column]
            else:
                column_to_parameter_dict[parameter_column] = parameter_column
        return column_to_parameter_dict

    def process_dataframe(self, input_parameters_dataframe, is_raw_output):
        results = []
        time_last_request = None
        session = requests.Session()
        for index, input_parameters_row in input_parameters_dataframe.iterrows():
            rows_count = 0
            self.initial_parameter_columns = {}
            for column_name in self.column_to_parameter_dict:
                parameter_name = self.column_to_parameter_dict[column_name]
                self.initial_parameter_columns.update({parameter_name: input_parameters_row.get(column_name)})
            updated_endpoint_parameters = copy.deepcopy(self.endpoint_parameters)
            updated_endpoint_parameters.update(self.initial_parameter_columns)
            logger.info("Processing row #{}, creating client with credential={}, updated_endpoint={}, custom_key_values={}".format(
                index + 1,
                logger.filter_secrets(self.credential_parameters),
                updated_endpoint_parameters,
                self.custom_key_values
            ))
            self.client = RestAPIClient(
                self.credential_parameters,
                updated_endpoint_parameters,
                custom_key_values=self.custom_key_values,
                session=session,
                behaviour_when_error=self.behaviour_when_error
            )
            self.client.time_last_request = time_last_request
            while self.client.has_more_data():
                page_results = self.retrieve_next_page(is_raw_output)
                results.extend(page_results)
                rows_count += len(page_results)
                if self.is_row_limit and rows_count >= self.maximum_number_rows:
                    break
            time_last_request = self.client.time_last_request
        return results

    def retrieve_next_page(self, is_raw_output):
        page_rows = []
        logger.info("retrieve_next_page: Calling next page")
        json_response = self.client.paginated_api_call(can_raise_exeption=self.can_raise)
        default_dict = {
            DKUConstants.REPONSE_ERROR_KEY: json_response.get(DKUConstants.REPONSE_ERROR_KEY, None)
        } if self.behaviour_when_error == "keep-error-column" else {}
        metadata = self.client.get_metadata() if self.display_metadata else default_dict
        is_api_returning_dict = True
        if self.extraction_key:
            data_rows = get_value_from_path(json_response, self.extraction_key.split("."), can_raise=False)
            if data_rows is None:
                if self.behaviour_when_error == "ignore":
                    return []
                error_message = "Extraction key '{}' was not found in the incoming data".format(self.extraction_key)
                if self.can_raise:
                    raise DataikuException(error_message)
                elif DKUConstants.REPONSE_ERROR_KEY in metadata:
                    return [metadata]
                else:
                    return self.format_page_rows([{DKUConstants.REPONSE_ERROR_KEY: error_message}], is_raw_output, metadata)
            page_rows.extend(self.format_page_rows(data_rows, is_raw_output, metadata))
        else:
            # Todo: check api_response key is free and add something overwise
            base_row = copy.deepcopy(metadata)
            if is_raw_output:
                if is_error_message(json_response):
                    base_row.update(parse_keys_for_json(json_response))
                else:
                    base_row.update({
                        DKUConstants.API_RESPONSE_KEY: json.dumps(json_response)
                    })
            else:
                if isinstance(json_response, dict):
                    base_row.update(parse_keys_for_json(json_response))
                elif isinstance(json_response, list):
                    is_api_returning_dict = False
                    for row in json_response:
                        base_row = copy.deepcopy(metadata)
                        base_row.update(parse_keys_for_json(row))
                        base_row.update(self.initial_parameter_columns)
                        page_rows.append(base_row)

            if is_api_returning_dict:
                base_row.update(self.initial_parameter_columns)
                page_rows.append(base_row)
        return page_rows

    def format_page_rows(self, data_rows, is_raw_output, metadata=None):
        page_rows = []
        metadata = metadata or {}
        for data_row in data_rows:
            base_row = copy.deepcopy(self.initial_parameter_columns)
            base_row.update(metadata)
            if is_raw_output:
                if is_error_message(data_row):
                    base_row.update({
                        DKUConstants.API_RESPONSE_KEY: None
                    })
                    base_row.update(parse_keys_for_json(data_row))
                else:
                    base_row.update({
                        DKUConstants.API_RESPONSE_KEY: json.dumps(data_row)
                    })
            else:
                base_row.update(parse_keys_for_json(data_row))
            page_rows.append(base_row)
        return page_rows


def is_error_message(jsons_response):
    if type(jsons_response) not in [dict, list]:
        return False
    if DKUConstants.REPONSE_ERROR_KEY in jsons_response and len(jsons_response) == 1:
        return True
    else:
        return False
