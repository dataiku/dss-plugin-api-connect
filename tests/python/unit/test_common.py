from dku_utils import template_dict
import pytest


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
