from dataiku.llm.agent_tools import BaseAgentTool
from safe_logger import SafeLogger
from dku_constants import DKUConstants
from rest_api_client import RestAPIClient
from dku_utils import (
    get_dku_key_values, get_endpoint_parameters,
    get_secure_credentials,
    decode_csv_data, decode_bytes, get_user_secrets
)
from jsonpath_ng.ext import parse


logger = SafeLogger("api-connect plugin", forbidden_keys=DKUConstants.FORBIDDEN_KEYS)


class CustomAgentTool(BaseAgentTool):
    def set_config(self, config, plugin_config):
        logger.info('API-Connect plugin agent tool v{}'.format(DKUConstants.PLUGIN_VERSION))
        logger.info("config={}, plugin_config={}".format(
                logger.filter_secrets(config),
                logger.filter_secrets(plugin_config)
            )
        )
        self.config = config
        tool_parameters = config.get("tool_parameters", [])
        self.properties = {}
        self.required = []
        self.parameters = []
        self.sample_query = {}
        for tool_parameter in tool_parameters:
            parameter_name = tool_parameter.get("tool_parameter_name")
            parameter_type = tool_parameter.get("tool_parameter_type")
            parameter_description = tool_parameter.get("tool_parameter_description")
            if parameter_name and parameter_type:
                self.sample_query[parameter_name] = parameter_description
                self.parameters.append(parameter_name)
                self.properties[parameter_name] = {
                    "type": parameter_type,
                    "description": parameter_description
                }
                if tool_parameter.get("tool_parameter_is_required", False):
                    self.required.append(parameter_name)

        self.endpoint_parameters = get_endpoint_parameters(config)
        self.secure_credentials = get_secure_credentials(config)
        self.credential = config.get("credential", {})
        self.custom_key_values = get_dku_key_values(config.get("custom_key_values", {}))
        user_secrets = get_user_secrets(config)
        self.custom_key_values.update(user_secrets)
        self.extraction_key = self.endpoint_parameters.get("extraction_key", "")
        self.extraction_path = self.extraction_key.split('.')

    def get_descriptor(self, tool):
        return {
            "description": "{}".format(self.config.get("tool_description", "")),
            "inputSchema": {
                "$id": "https://example.com/agents/tools/hash/input",
                "title": "Input for the hashing tool",
                "type": "object",
                "properties": self.properties,
                "required": self.required
            }
        }

    def invoke(self, input, trace):
        args = input.get("input", {})
        self.custom_key_values.update(args)
        client = RestAPIClient(self.credential, self.secure_credentials, self.endpoint_parameters, self.custom_key_values)
        rows = []
        while client.has_more_data():
            json_response = client.paginated_api_call()
            if self.extraction_key:
                matches = parse(self.extraction_key).find(json_response)
                data = []
                for counter in range(0, len(matches)):
                    data.append(matches[counter].value)
            else:
                data = json_response
            for formated_row in format_data(data):
                rows.append(formated_row)
        return {
            "output": "{}".format(rows),
            "sources":  [{
                "toolCallDescription": "Payload was hashed"
            }]
        }

    def load_sample_query(self, tool):
        return self.sample_query


def format_data(data):
    if isinstance(data, list):
        for row in data:
            yield row
    elif isinstance(data, dict):
        yield data
    else:
        csv_data = decode_csv_data(data)
        if csv_data:
            for row in csv_data:
                yield row
        else:
            yield {
                DKUConstants.API_RESPONSE_KEY: "{}".format(decode_bytes(data))
            }
