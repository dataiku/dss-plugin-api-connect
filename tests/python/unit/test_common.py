from dku_utils import template_dict, join_url
from rest_api_client import RestAPIClient
from retry_handler import RetryHandler
import pytest
import requests


class FakeSession:
    def __init__(self, responses, request_times, clock):
        self.responses = iter(responses)
        self.request_times = request_times
        self.clock = clock

    def request(self, *args, **kwargs):
        self.request_times.append(self.clock[0])
        return next(self.responses)


def response_with_status(status_code):
    response = requests.Response()
    response.status_code = status_code
    return response


class TestCommonMethods:
    def setup_class(self):
        self.template = {
            'url': 'https://api.spotify.com/v1/users/{{user_id}}/playlists',
            'headers': {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {{access_token}}'
            },
            'recipe_columns_parameter_names': ['user_id'],
            'key_to_next_page_url': 'next', 'items_key': 'items'
        }
        self.kwargs = {
            u'column': u'profiles id',
            'access_token': u'12341234secretcode-4321shhhhhh',
            'user_id': '1234abcde'
        }
        self.endpoint_ok = {
            'url': 'https://api.spotify.com/v1/users/1234abcde/playlists',
            'headers': {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer 12341234secretcode-4321shhhhhh'
            },
            'key_to_next_page_url': 'next',
            'items_key': 'items',
            'recipe_columns_parameter_names': ['user_id']
        }

    def test_template_dict(self):
        endpoint = template_dict(self.template, **self.kwargs)
        assert endpoint == self.endpoint_ok

    def test_join_url(self):
        assert "https://bla.com/bla/bli" == join_url("https://bla.com", "bla/bli")
        assert "https://bla.com/bla/bli" == join_url("https://bla.com/", "bla/bli")
        assert "https://bla.com/bla/bli" == join_url("https://bla.com/", "/bla/bli")
        assert "https://bla.com/bla/bli" == join_url("https://bla.com/", "bla/bli")
        assert "https://bla.com/bla/bli/" == join_url("https://bla.com", "bla/bli/")
        assert "https://bla.com/bla/bli/" == join_url("https://bla.com/", "bla/bli/")
        assert "https://bla.com/bla/bli/" == join_url("https://bla.com/", "/bla/bli/")
        assert "https://bla.com/bla/bli/" == join_url("https://bla.com/", "bla/bli/")
        assert "https://bla.com" == join_url("https://bla.com/", "")
        assert "https://bla.com" == join_url("https://bla.com/", None)
        assert "https://bla.com" == join_url("https://bla.com", "")
        assert "https://bla.com" == join_url("https://bla.com", None)

    def run_retry_with_virtual_clock(self, monkeypatch, time_between_requests, backoff_type, initial_delay,
                                     maximum_number_of_retries, response_codes):
        clock = [0]
        sleep_durations = []
        request_times = []

        def sleep(duration):
            sleep_durations.append(duration)
            clock[0] += duration

        monkeypatch.setattr("rest_api_client.time.time", lambda: clock[0])
        monkeypatch.setattr("rest_api_client.time.sleep", sleep)

        client = object.__new__(RestAPIClient)
        client.retry_handler = RetryHandler(
            backoff_type=backoff_type,
            initial_delay=initial_delay,
            maximum_number_of_retries=maximum_number_of_retries,
            status_codes_to_retry=["503"],
        )
        client.time_between_requests = time_between_requests
        client.time_last_request = None
        client.session = FakeSession(
            [response_with_status(status_code) for status_code in response_codes],
            request_times,
            clock,
        )

        client.request_with_errors_retry("GET", "https://example.test")

        return request_times, sleep_durations

    def test_exponential_retries_use_the_greater_of_backoff_and_throttle(self, monkeypatch):
        request_times, _ = self.run_retry_with_virtual_clock(
            monkeypatch,
            time_between_requests=60,
            backoff_type="exponential",
            initial_delay=30,
            maximum_number_of_retries=5,
            response_codes=[503, 503, 503, 503, 503, 200],
        )

        assert request_times == [0, 60, 120, 240, 480, 960]

    def test_linear_retry_respects_throttling_rate_and_retry_budget(self, monkeypatch):
        request_times, sleep_durations = self.run_retry_with_virtual_clock(
            monkeypatch,
            time_between_requests=30,
            backoff_type="linear",
            initial_delay=5,
            maximum_number_of_retries=5,
            response_codes=[503, 503, 503, 503, 503, 200],
        )

        assert request_times == [0, 30, 60, 90, 120, 150]
        assert sleep_durations == [5, 25, 5, 25, 5, 25, 5, 25, 5, 25]

    def test_retry_does_not_make_another_request_after_exhausting_the_budget(self, monkeypatch):
        request_times, _ = self.run_retry_with_virtual_clock(
            monkeypatch,
            time_between_requests=60,
            backoff_type="linear",
            initial_delay=1,
            maximum_number_of_retries=5,
            response_codes=[503, 503, 503, 503, 503, 503],
        )

        assert request_times == [0, 60, 120, 180, 240, 300]
