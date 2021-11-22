from dataiku.customstep import get_plugin_config
from safe_logger import SafeLogger
from rest_api_client import RestAPIClient
from dku_utils import get_dku_key_values, get_endpoint_parameters


logger = SafeLogger("api-connect plugin", forbiden_keys=["token", "password"])

# settings at the plugin level (set by plugin administrators in the Plugins section)
plugin_config = get_plugin_config()
config = plugin_config.get("config", {})
logger.info("config={}".format(logger.filter_secrets(config)))
endpoint_parameters = get_endpoint_parameters(config)
credential = config.get("credential", {})
custom_key_values = get_dku_key_values(config.get("custom_key_values", {}))
client = RestAPIClient(credential, endpoint_parameters, custom_key_values)
client.has_more_data()
json_response = client.paginated_api_call()
logger.info(json_response)
