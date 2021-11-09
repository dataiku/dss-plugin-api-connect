from dku_plugin_test_utils import dss_scenario

TEST_PROJECT_KEY = "PLUGINTESTAPICONNECT"


def test_run_api_connect_authentication_modes(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="AuthenticationModes")


def test_run_api_connect_pagination_modes(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="PAGINATION")


def test_run_api_connect_recipes(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="Recipes")


def test_run_api_connect_using_global_variable(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="UsingGlobalVariable")


def test_run_api_connect_array_api(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="ArrayAPI")
