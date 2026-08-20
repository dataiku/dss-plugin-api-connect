#!/usr/bin/env python3
"""Run the descriptor-driven DSS Compose stack and host-side pytest suite."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from support.integration_matrix import docker_python_versions, read_interpreters


ROOT = Path(__file__).resolve().parents[3]
COMPOSE = ("docker", "compose", "-f", "docker-compose.integration-tests.yaml")


def command(*parts: str, env: dict[str, str]) -> None:
    subprocess.run(parts, cwd=ROOT, env=env, check=True)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-dss", action="store_true")
    parser.add_argument("pytest_args", nargs="*")
    arguments = parser.parse_args(argv)

    if sys.version_info < (3, 11):
        raise SystemExit("The DevX integration runner requires Python 3.11 or newer")

    interpreters = read_interpreters(ROOT / "code-env/python/desc.json")
    project_archive = Path(os.environ.get("PROJECT_ARCHIVE_HOST", ROOT / "config/project.zip"))
    license_file = Path(os.environ.get("DSS_LICENSE_FILE", ROOT / "config/license.json"))
    if not project_archive.is_file():
        raise SystemExit(f"Project archive was not found: {project_archive}")
    if not license_file.is_file():
        raise SystemExit(f"DSS license was not found: {license_file}")
    if shutil.which("docker") is None:
        raise SystemExit("docker is required to run integration tests")

    environment = os.environ.copy()
    environment.update(
        {
            "EXTRA_DSS_PY_VERSIONS": " ".join(docker_python_versions(interpreters)),
            "DSS_VERSION": environment.get("DSS_VERSION", "14.7.0"),
            "DKU_DSS_URL": environment.get("DKU_DSS_URL", "http://localhost:10000"),
            "DSS_LICENSE_FILE": str(license_file.resolve()),
            "PROJECT_ARCHIVE_HOST": str(project_archive.resolve()),
            "PLUGIN_ID": environment.get("PLUGIN_ID", "api-connect"),
            "PROJECT_KEY": environment.get("PROJECT_KEY", "PLUGINTESTAPICONNECT"),
            "PYTEST_COMPATIBILITY_RESULT": environment.get(
                "PYTEST_COMPATIBILITY_RESULT", str(ROOT / ".ci/integration/compatibility.json")
            ),
            "DSS_USE_DOCKER_INSTANCE": "1",
            "PYTEST_RUNTIME_INSTANCE_CONFIG": str(
                ROOT / ".ci/integration/docker-instance.json"
            ),
        }
    )
    command(*COMPOSE, "up", "--build", "--wait", "dss", env=environment)
    try:
        command("make", "plugin", env=environment)
        command(
            sys.executable,
            "-m",
            "pytest",
            "tests/python/integration",
            *arguments.pytest_args,
            env=environment,
        )
    finally:
        if not arguments.keep_dss:
            subprocess.run((*COMPOSE, "down", "--volumes", "--remove-orphans"), cwd=ROOT, env=environment)


if __name__ == "__main__":
    main()
