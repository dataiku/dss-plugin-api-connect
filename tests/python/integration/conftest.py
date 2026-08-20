"""Pytest fixtures for a disposable descriptor-driven DSS integration matrix."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "tests/tasks/config/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from integration_setup import DSSIntegrationSetup, DSSSetupError  # noqa: E402
from support.integration_matrix import CompatibilityResult, read_interpreters  # noqa: E402


def _connections() -> list[dict[str, str]]:
    raw = os.environ.get("CONNECTIONS_JSON", "[]")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise pytest.UsageError("CONNECTIONS_JSON must be valid JSON") from error
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise pytest.UsageError("CONNECTIONS_JSON must be an array of objects")
    required = {"name", "type"}
    if any(not required <= set(item) or not all(isinstance(item[key], str) for key in required) for item in value):
        raise pytest.UsageError("Every CONNECTIONS_JSON item requires string name and type")
    return value


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("dss-integration")
    group.addoption("--dss-project-archive", default=os.environ.get("PROJECT_ARCHIVE_HOST", str(ROOT / "config/project.zip")))
    group.addoption("--dss-license-file", default=os.environ.get("DSS_LICENSE_FILE", str(ROOT / "config/license.json")))
    group.addoption("--dss-plugin-archive", default=os.environ.get("PLUGIN_ARCHIVE", str(ROOT / "dist/dss-plugin-api-connect-1.5.0.zip")))
    group.addoption("--dss-plugin-id", default=os.environ.get("PLUGIN_ID", "api-connect"))
    group.addoption("--dss-project-key", default=os.environ.get("PROJECT_KEY", "PLUGINTESTAPICONNECT"))


def _configured_instance() -> tuple[Path, str, str] | None:
    """Read a user-supplied target without modifying its configuration file."""
    if os.environ.get("DSS_USE_DOCKER_INSTANCE") == "1":
        return None
    path = Path(
        os.environ.get(
            "PLUGIN_INTEGRATION_TEST_INSTANCE",
            ROOT / ".ci/integration/instance.json",
        )
    )
    if not path.is_file():
        return None
    try:
        targets = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(targets, dict) or len(targets) != 1:
            raise ValueError("exactly one target is required")
        target = next(iter(targets.values()))
        users = target["users"]
        api_key = users[users["default"]]
        url = target["url"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise pytest.UsageError(f"Invalid DSS instance configuration {path}: {error}") from error
    if not isinstance(url, str) or not isinstance(api_key, str):
        raise pytest.UsageError(
            f"Invalid DSS instance configuration {path}: url and API key must be strings"
        )
    return path, url.rstrip("/"), api_key


def _prepare_dss(config: pytest.Config) -> dict[str, Any]:
    project_archive = Path(config.getoption("dss_project_archive"))
    license_file = Path(config.getoption("dss_license_file"))
    plugin_archive = Path(config.getoption("dss_plugin_archive"))
    for label, path in (("project archive", project_archive), ("license", license_file), ("plugin archive", plugin_archive)):
        if not path.is_file():
            raise pytest.UsageError(f"DSS {label} was not found: {path}")

    configured_instance = _configured_instance()
    if configured_instance is not None:
        config_file, url, api_key = configured_instance
        if _connections():
            raise pytest.UsageError(
                "CONNECTIONS_JSON requires Docker bootstrap credentials; "
                "do not use it with a preconfigured DSS instance"
            )
        setup = DSSIntegrationSetup(url)
        try:
            client = setup.client(api_key)
            setup.grant_admin_designer(client)
            setup.import_project(client, project_archive, config.getoption("dss_project_key"))
            setup.install_plugin(client, config.getoption("dss_plugin_id"), plugin_archive)
            os.environ["PLUGIN_INTEGRATION_TEST_INSTANCE"] = str(config_file)
            return {
                "client": client,
                "plugin_id": config.getoption("dss_plugin_id"),
                "results": [],
            }
        except DSSSetupError as error:
            raise pytest.UsageError(str(error)) from error
        finally:
            setup.close()

    setup = DSSIntegrationSetup(os.environ.get("DKU_DSS_URL", "http://localhost:10000"))
    try:
        setup.register_license(license_file)
        setup.authenticate()
        api_key = setup.create_api_key()
        client = setup.client(api_key)
        setup.grant_admin_designer(client)
        setup.create_connections(_connections(), ROOT / "tests/tasks/config/templates/connections")
        setup.import_project(client, project_archive, config.getoption("dss_project_key"))
        setup.install_plugin(client, config.getoption("dss_plugin_id"), plugin_archive)
        instance = {
            "pytest": {
                "url": os.environ["DKU_DSS_URL"],
                "users": {"admin": api_key, "default": "admin"},
                "python_interpreter": list(read_interpreters(ROOT / "code-env/python/desc.json")),
            }
        }
        config_file = Path(
            os.environ.get(
                "PYTEST_RUNTIME_INSTANCE_CONFIG",
                ROOT / ".ci/integration/docker-instance.json",
            )
        )
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(instance), encoding="utf-8")
        os.environ["PLUGIN_INTEGRATION_TEST_INSTANCE"] = str(config_file)
        return {
            "client": client,
            "plugin_id": config.getoption("dss_plugin_id"),
            "results": [],
        }
    except DSSSetupError as error:
        raise pytest.UsageError(str(error)) from error
    finally:
        setup.close()


def pytest_configure(config: pytest.Config) -> None:
    # dataiku-plugin-tests-utils reads PLUGIN_INTEGRATION_TEST_INSTANCE while
    # collecting tests, so DSS setup must finish before collection begins.
    config._compatibility_results = []  # type: ignore[attr-defined]
    config._dss_prepared = _prepare_dss(config)  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def interpreters() -> tuple[str, ...]:
    return read_interpreters(ROOT / "code-env/python/desc.json")


@pytest.fixture(scope="session")
def prepared_dss(request: pytest.FixtureRequest) -> dict[str, Any]:
    return request.config._dss_prepared  # type: ignore[attr-defined]


@pytest.fixture(scope="session", params=read_interpreters(ROOT / "code-env/python/desc.json"), ids=str)
def python_interpreter(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture(scope="session")
def compatibility_lane(prepared_dss: dict[str, Any], python_interpreter: str) -> CompatibilityResult:
    result = CompatibilityResult(interpreter=python_interpreter)
    plugin = prepared_dss["client"].get_plugin(prepared_dss["plugin_id"])
    try:
        creation = plugin.create_code_env(python_interpreter=python_interpreter).wait_for_result()
        name = creation.get("envName") if isinstance(creation, dict) else None
        if not name:
            raise DSSSetupError(f"DSS did not create an environment: {creation!r}")
        environments = prepared_dss["client"].list_code_envs()
        environment = next((item for item in environments if item.get("envName") == name), None)
        if environment is None or environment.get("pythonInterpreter") != python_interpreter:
            raise DSSSetupError(f"DSS did not create {python_interpreter}: {environment!r}")
        settings = plugin.get_settings()
        settings.set_code_env(name)
        settings.save()
        result.environment_name = name
    except Exception as error:
        result.setup_error = str(error)
        prepared_dss["results"].append(result)
        pytest.skip(f"{python_interpreter} environment setup failed: {error}")
    prepared_dss["results"].append(result)
    return result


@pytest.fixture(scope="session", autouse=True)
def activate_compatibility_lane(compatibility_lane: CompatibilityResult) -> CompatibilityResult:
    """Associate the interpreter-specific environment before any scenario runs."""
    return compatibility_lane


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]):
    outcome = yield
    report = outcome.get_result()
    lane = item.funcargs.get("compatibility_lane") if hasattr(item, "funcargs") else None
    if report.when == "call" and report.failed and isinstance(lane, CompatibilityResult):
        lane.scenario_failures = (lane.scenario_failures or []) + [item.nodeid]


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    prepared = getattr(session.config, "_dss_prepared", None)
    if not isinstance(prepared, dict):
        return
    results: list[CompatibilityResult] = prepared["results"]
    result_path = Path(os.environ.get("PYTEST_COMPATIBILITY_RESULT", ROOT / ".ci/integration/compatibility.json"))
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps({"results": [item.as_dict() for item in results]}, indent=2) + "\n", encoding="utf-8")
    if any(not item.success for item in results) and exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_terminal_summary(terminalreporter: Any) -> None:
    prepared = getattr(terminalreporter.config, "_dss_prepared", None)
    if not isinstance(prepared, dict):
        return
    results: list[CompatibilityResult] = prepared["results"]
    if not results:
        return
    terminalreporter.write_sep("-", "DSS Python compatibility")
    for result in results:
        status = "PASS" if result.success else "FAIL"
        detail = result.environment_name or result.setup_error or "scenario failure"
        terminalreporter.write_line(f"{status:4} {result.interpreter}: {detail}")
