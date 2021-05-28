from dataikuapi.utils import DataikuException
from rest_api_client import RestAPIClient
from safe_logger import SafeLogger
import copy

logger = SafeLogger("api-connect plugin", forbiden_keys=["token", "password"])


class RestApiRecipeSession:
    def __init__(self, custom_key_values, credential_parameters, endpoint_parameters, extraction_key, parameter_columns, parameter_renamings):
        self.custom_key_values = custom_key_values
        self.credential_parameters = credential_parameters
        self.endpoint_parameters = endpoint_parameters
        self.extraction_key = extraction_key
        self.client = None
        self.initial_parameter_columns = None
        self.column_to_parameter_dict = self.get_column_to_parameter_dict(parameter_columns, parameter_renamings)

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
        for index, input_parameters_row in input_parameters_dataframe.iterrows():
            self.initial_parameter_columns = {}
            for column_name in self.column_to_parameter_dict:
                parameter_name = self.column_to_parameter_dict[column_name]
                self.initial_parameter_columns.update({parameter_name: input_parameters_row.get(column_name)})
            updated_endpoint_parameters = copy.deepcopy(self.endpoint_parameters)
            updated_endpoint_parameters.update(self.initial_parameter_columns)
            logger.info("Creating client with credential={}, updated_endpoint={}, custom_key_values={}".format(
                logger.filter_secrets(self.credential_parameters),
                updated_endpoint_parameters,
                self.custom_key_values
            ))
            self.client = RestAPIClient(self.credential_parameters, updated_endpoint_parameters, custom_key_values=self.custom_key_values)
            self.client.time_last_request = time_last_request
            while self.client.has_more_data():
                page_results = self.retrieve_next_page(is_raw_output)
                results.extend(page_results)
            time_last_request = self.client.time_last_request
        return results

    def retrieve_next_page(self, is_raw_output):
        page_rows = []
        base_row = copy.deepcopy(self.initial_parameter_columns)
        logger.info("retrieve_next_page: Calling next page")
        json_response = self.client.paginated_api_call(can_raise_exeption=False)
        if self.extraction_key:
            data_rows = json_response.get(self.extraction_key, [json_response])
            if data_rows is None:
                raise DataikuException("Extraction key '{}' was not found in the incoming data".format(self.extraction_key))
            page_rows.extend(self.format_page_rows(data_rows, is_raw_output))
        else:
            # Todo: check api_response key is free and add something overwise
            if is_raw_output:
                if is_error_message(json_response):
                    base_row.update(json_response)
                else:
                    base_row.update({"api_response": json_response})
            else:
                base_row.update(json_response)
            page_rows.append(base_row)
        return page_rows

    def format_page_rows(self, data_rows, is_raw_output):
        page_rows = []
        for data_row in data_rows:
            base_row = copy.deepcopy(self.initial_parameter_columns)
            if is_raw_output:
                if is_error_message(data_row):
                    base_row.update(data_row)
                else:
                    base_row.update({"api_response": data_row})
            else:
                base_row.update(data_row)
            page_rows.append(base_row)
        return page_rows


def is_error_message(jsons_response):
    if "error" in jsons_response and len(jsons_response) == 1:
        return True
    else:
        return False
