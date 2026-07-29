import requests
import time
from safe_logger import SafeLogger


logger = SafeLogger("api-connect plugin retry handler")


class DefaultRetryHandler():
    def __init__(self):
        self.number_of_tries = 0

    def should_retry(self, response):
        self.number_of_tries += 1
        if self.number_of_tries == 1:
            return True
        return False


class RetryHandler():
    def __init__(self, backoff_type=None, initial_delay=None, maximum_number_of_retries=None,
                 maximum_duration_of_retry=None, status_codes_to_retry=None):
        self.backoff_type = None
        if backoff_type in ["linear", "exponential"]:
            self.backoff_type = backoff_type
        self.initial_delay = 0
        if isinstance(initial_delay, int):
            self.initial_delay = initial_delay
        self.maximum_number_of_retries = None
        if isinstance(maximum_number_of_retries, int):
            self.maximum_number_of_retries = maximum_number_of_retries
        self.maximum_duration_of_retry = None
        if isinstance(maximum_duration_of_retry, int):
            self.maximum_duration_of_retry = maximum_duration_of_retry
        self.next_delay = None
        self.status_codes_to_retry = []
        if isinstance(status_codes_to_retry, list):
            self.status_codes_to_retry = status_codes_to_retry
        self.number_of_tries = 0
        #Retry handler initialised with None/1/None/10/['429']/
        logger.info("Retry handler initialised with {}/{}/{}/{}/{}/".format(
            self.backoff_type,
            self.initial_delay,
            self.maximum_number_of_retries,
            self.maximum_duration_of_retry,
            self.status_codes_to_retry
        ))

    def should_retry(self, response):
        logger.info("Should retry?")
        if self.number_of_tries == 0:
            logger.info("Initial try: should.")
            self.number_of_tries = 1
            return True
        if isinstance(response, requests.Response):
            logger.info("is response")
            status_code = str(response.status_code)
            logger.info("status_code={}".format(status_code))
            if status_code in self.status_codes_to_retry:
                logger.warning("HTTP error {}. Retrying.".format(status_code))
                self._compute_next_delay()
                if self._is_next_delay_too_long():
                    logger.info("_is_next_delay_too_long: should not.")
                    return False
                if self._too_many_retries():
                    logger.info("_too_many_retries: should not.")
                    return False
                self._sleep()
                return True
        return False

    def _compute_next_delay(self):
        self.number_of_tries += 1
        if self.next_delay is None:
            self.next_delay = self.initial_delay
            return
        if self.backoff_type=="linear":
            # delay is same as last try
            return
        if self.backoff_type=="exponential":
            self.next_delay = self.next_delay * 2

    def _sleep(self):
        if isinstance(self.next_delay, int):
            logger.warning("Sleeping for {}s".format(self.next_delay))
            time.sleep(self.next_delay)

    def _too_many_retries(self):
        if not self.maximum_number_of_retries:
            return False
        if self.number_of_tries > self.maximum_number_of_retries:
            logger.warning("Maximum number of retries reached. Not retrying.")
            return True
        return False

    def _is_next_delay_too_long(self):
        if not self.maximum_duration_of_retry:
            return False
        if self.next_delay >= self.maximum_duration_of_retry:
            logger.warning("Sleep time before retry reached the max. Not retrying.")
            return True
        return False
