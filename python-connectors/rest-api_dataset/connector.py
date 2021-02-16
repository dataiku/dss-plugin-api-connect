from dataiku.connector import Connector
from dataikuapi.utils import DataikuException
from safe_logger import SafeLogger
from rest_api_client import RestAPIClient
from dku_utils import get_dku_key_values

logger = SafeLogger("rest-api plugin", forbiden_keys=["token", "password"])


class RestAPIConnector(Connector):

    def __init__(self, config, plugin_config):
        Connector.__init__(self, config, plugin_config)  # pass the parameters to the base class

        logger.info("config={}".format(logger.filter_secrets(config)))
        endpoint = config.get("endpoint", {})
        credential = config.get("credential", {})
        custom_key_values = get_dku_key_values(config.get("custom_key_values", {}))
        self.client = RestAPIClient(credential, endpoint, custom_key_values)
        extraction_key = endpoint.get("extraction_key", None)
        if extraction_key == '':
            extraction_key = None
        self.extraction_key = extraction_key
        self.raw_output = endpoint.get("raw_output", None)

    def get_read_schema(self):
        # In this example, we don't specify a schema here, so DSS will infer the schema
        # from the columns actually returned by the generate_rows method
        return None

    def generate_rows(self, dataset_schema=None, dataset_partitioning=None,
                      partition_id=None, records_limit=-1):
        while self.client.has_more_data():
            json_response = self.client.paginated_api_call()
            if self.extraction_key is None:
                # Todo: check api_response key is free and add something overwise
                if isinstance(json_response, list):
                    for row in json_response:
                        yield {"api_response": row}
                else:
                    yield {"api_response": json_response}
            else:
                data = json_response.get(self.extraction_key, None)
                if data is None:
                    raise DataikuException("Extraction key '{}' was not found in the incoming data".format(self.extraction_key))
                for result in data:
                    if self.raw_output:
                        yield {"api_reply": result}
                    else:
                        yield result

    def get_writer(self, dataset_schema=None, dataset_partitioning=None,
                   partition_id=None):
        """
        Returns a writer object to write in the dataset (or in a partition).

        The dataset_schema given here will match the the rows given to the writer below.

        Note: the writer is responsible for clearing the partition, if relevant.
        """
        raise DataikuException("Unimplemented")

    def get_partitioning(self):
        """
        Return the partitioning schema that the connector defines.
        """
        raise DataikuException("Unimplemented")

    def list_partitions(self, partitioning):
        """Return the list of partitions for the partitioning scheme
        passed as parameter"""
        return []

    def partition_exists(self, partitioning, partition_id):
        """Return whether the partition passed as parameter exists

        Implementation is only required if the corresponding flag is set to True
        in the connector definition
        """
        raise DataikuException("unimplemented")

    def get_records_count(self, partitioning=None, partition_id=None):
        """
        Returns the count of records for the dataset (or a partition).

        Implementation is only required if the corresponding flag is set to True
        in the connector definition
        """
        raise DataikuException("unimplemented")


class CustomDatasetWriter(object):
    def __init__(self):
        return

    def write_row(self, row):
        """
        Row is a tuple with N + 1 elements matching the schema passed to get_writer.
        The last element is a dict of columns not found in the schema
        """
        raise DataikuException("unimplemented")

    def close(self):
        return
