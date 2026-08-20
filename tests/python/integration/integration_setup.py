"""Importable DSS setup services for the host-side pytest integration suite."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests


class DSSSetupError(RuntimeError):
    """A setup action failed and pytest must not run against partial state."""


class DSSIntegrationSetup:
    """Bootstrap DSS, then use the internal ``dataiku`` client for DSS APIs."""

    def __init__(self, base_url: str, login: str = "admin", password: str = "admin"):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/dip/api"
        self.login_name = login
        self.password = password
        self.session = requests.Session()
        self.headers: dict[str, str] = {}

    def close(self) -> None:
        self.session.close()

    def register_license(self, license_file: Path) -> None:
        payload = json.loads(license_file.read_text(encoding="utf-8"))
        response = self.session.post(
            f"{self.api_url}/registration/initial-register-community",
            data={
                "userFirstName": "Robin",
                "userLastName": "Barker",
                "userEmail": "robin.barker@darmaiku.ai",
                "instanceId": payload["content"]["instanceId"],
                "license": json.dumps(payload),
            },
        )
        if response.status_code <= 399:
            return
        message = _response_message(response)
        if message != "DSS is already registered":
            raise DSSSetupError(f"DSS license registration failed: {message}")

    def authenticate(self) -> None:
        response = self.session.post(
            f"{self.api_url}/login",
            data={"login": self.login_name, "password": self.password},
        )
        _require_success(response, "DSS login")
        _require_success(
            self.session.get(f"{self.api_url}/get-configuration"),
            "DSS configuration",
        )
        token = next(
            (
                value
                for key, value in self.session.cookies.items()
                if key.startswith("dss_xsrf_token")
            ),
            None,
        )
        if not token:
            raise DSSSetupError("DSS login did not provide an XSRF token")
        self.headers = {"X-Xsrf-Token": token}

    def create_api_key(self) -> str:
        """Create the bootstrap API key; the internal client needs this credential."""
        response = self.session.post(
            f"{self.api_url}/publicapi/create-personal-api-key",
            data={"label": "pytest integration matrix", "description": ""},
            headers=self.headers,
        )
        _require_success(response, "DSS API-key creation")
        key = response.json().get("key")
        if not isinstance(key, str) or not key:
            raise DSSSetupError("DSS API-key creation did not return a key")
        return key

    def client(self, api_key: str) -> Any:
        """Return the DevX internal ``dataiku`` client configured for this DSS."""
        os.environ["DKU_DSS_URL"] = self.base_url
        os.environ["DKU_API_KEY"] = api_key
        import dataiku  # type: ignore[import-untyped]

        return dataiku.api_client()

    def grant_admin_designer(self, client: Any) -> None:
        user = client.get_user("admin")
        settings = user.get_settings()
        settings.get_raw()["userProfile"] = "FULL_DESIGNER"
        settings.save()

    def create_connections(self, connections: list[dict[str, str]], templates: Path) -> None:
        for connection in connections:
            name, conn_type = connection["name"], connection["type"]
            template = templates / f"{_snake(conn_type)}.json"
            if not template.is_file():
                raise DSSSetupError(
                    f"No connection template for {conn_type!r}: {template}"
                )
            definition = json.loads(template.read_text(encoding="utf-8"))
            fields = _render(definition.get("fields", {}), connection)
            for key in definition.get("json_stringify", []):
                fields[key] = json.dumps(fields[key], separators=(",", ":"))
            response = self.session.post(
                f"{self.api_url}/admin/connections/save",
                data=fields,
                headers={
                    **self.headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                },
            )
            _require_success(response, f"creation of connection {name!r}")

    def import_project(self, client: Any, archive_path: Path, project_key: str) -> None:
        with archive_path.open("rb") as archive:
            result = client.prepare_project_import(archive).execute(
                {"targetProjectKey": project_key}
            )
        if not isinstance(result, dict) or not result.get("success"):
            raise DSSSetupError(f"Project import failed: {result!r}")

    def install_plugin(self, client: Any, plugin_id: str, archive_path: Path) -> None:
        with archive_path.open("rb") as archive:
            result = client.start_install_plugin_from_archive(archive).wait_for_result()
        if not isinstance(result, dict) or not result.get("success"):
            raise DSSSetupError(f"Plugin installation failed: {result!r}")
        if not any(plugin.get("id") == plugin_id for plugin in client.list_plugins()):
            raise DSSSetupError(f"Installed plugin {plugin_id!r} was not listed by DSS")


def _snake(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "_", value.strip()).strip("_").lower()


def _render(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, str):
        return value.format(**mapping)
    if isinstance(value, list):
        return [_render(item, mapping) for item in value]
    if isinstance(value, dict):
        return {key: _render(item, mapping) for key, item in value.items()}
    return value


def _response_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or response.reason
    return str(payload.get("message", payload)) if isinstance(payload, dict) else str(payload)


def _require_success(response: requests.Response, action: str) -> None:
    if response.status_code > 399:
        raise DSSSetupError(f"{action} failed: {_response_message(response)}")
