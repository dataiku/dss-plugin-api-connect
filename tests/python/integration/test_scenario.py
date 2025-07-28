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


def test_run_api_connect_search_path(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="SearchPath")


def test_run_api_connect_redirection(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="REDIRECTION")


def test_run_api_connect_check_sc_84465(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="CHECKSC84465")


def test_run_api_connect_ntlm_authentication(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="NTLMAUTHENTICATION")


def test_run_api_connect_relative_url_pagination(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="RELATIVEURLPAGINATION")


def test_run_api_connect_check_sc_110446(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="CHECKSC110446")


def test_run_api_connect_check_sc_163656_error_column_always_in_schema(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="SC163656")


def test_run_api_connect_xml_handling(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="XML_HANDLING")


def test_run_api_connect_parameters_renaming(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="COLUMNPARAMETERRENAMING")
