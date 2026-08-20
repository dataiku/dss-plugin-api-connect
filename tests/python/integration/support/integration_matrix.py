"""Repository-specific support for the DSS pytest compatibility matrix."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class MatrixConfigurationError(ValueError):
    """Raised for invalid repository integration-test configuration."""


def read_interpreters(descriptor_path: Path) -> tuple[str, ...]:
    """Read ordered, unique DSS interpreter labels from a plugin descriptor."""
    try:
        descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise MatrixConfigurationError(f"Descriptor was not found: {descriptor_path}") from error
    except json.JSONDecodeError as error:
        raise MatrixConfigurationError(f"Invalid JSON descriptor: {descriptor_path}") from error

    labels = descriptor.get("acceptedPythonInterpreters") if isinstance(descriptor, dict) else None
    if not isinstance(labels, list) or not labels:
        raise MatrixConfigurationError("acceptedPythonInterpreters must be a non-empty list")
    if len(labels) != len(set(labels)):
        raise MatrixConfigurationError("acceptedPythonInterpreters must not contain duplicates")

    validated: list[str] = []
    for label in labels:
        if not isinstance(label, str) or not label.startswith("PYTHON3"):
            raise MatrixConfigurationError(f"Unsupported Python interpreter label: {label!r}")
        digits = label[len("PYTHON"):]
        if len(digits) < 2 or not digits.isdigit():
            raise MatrixConfigurationError(f"Malformed Python interpreter label: {label!r}")
        validated.append(label)
    return tuple(validated)


def docker_python_versions(interpreters: tuple[str, ...]) -> tuple[str, ...]:
    """Convert DSS labels such as PYTHON313 into Docker package versions."""
    return tuple(f"{label[6]}.{label[7:]}" for label in interpreters)


@dataclass
class CompatibilityResult:
    interpreter: str
    environment_name: str | None = None
    setup_error: str | None = None
    scenario_failures: list[str] | None = None

    @property
    def success(self) -> bool:
        return self.setup_error is None and not self.scenario_failures

    def as_dict(self) -> dict[str, Any]:
        return {
            "interpreter": self.interpreter,
            "environment_name": self.environment_name,
            "setup_error": self.setup_error,
            "scenario_failures": self.scenario_failures or [],
            "success": self.success,
        }
