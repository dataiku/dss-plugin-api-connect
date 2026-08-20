#!/usr/bin/env python3
"""Install API Connect and verify all descriptor-declared Python environments."""

import argparse
import json
import os
import sys

import dataikuapi

from support.code_env_verifier import failed_results, verify_plugin_code_environments


def _read_interpreters(descriptor_path):
    with open(descriptor_path, "r") as descriptor_file:
        descriptor = json.load(descriptor_file)
    interpreters = descriptor.get("acceptedPythonInterpreters")
    if not isinstance(interpreters, list) or not interpreters:
        raise ValueError("acceptedPythonInterpreters must be a non-empty list")
    if len(interpreters) != len(set(interpreters)):
        raise ValueError("acceptedPythonInterpreters must not contain duplicates")
    for interpreter in interpreters:
        if not isinstance(interpreter, str) or not interpreter.startswith("PYTHON3"):
            raise ValueError("unsupported Python interpreter label: {0!r}".format(interpreter))
        digits = interpreter[len("PYTHON"):]
        if len(digits) < 2 or not digits.isdigit():
            raise ValueError("malformed Python interpreter label: {0!r}".format(interpreter))
    return interpreters


def _read_target(instance_config_path):
    with open(instance_config_path, "r") as config_file:
        targets = json.load(config_file)
    if not isinstance(targets, dict) or len(targets) != 1:
        raise ValueError("instance configuration must contain exactly one DSS target")
    target = next(iter(targets.values()))
    users = target.get("users", {})
    default_user = users.get("default")
    api_key = users.get(default_user)
    if not target.get("url") or not api_key:
        raise ValueError("DSS target must define url and users.default API key")
    return target["url"], api_key


def _install_plugin(client, archive_path):
    with open(archive_path, "rb") as archive_file:
        installation = client.start_install_plugin_from_archive(archive_file)
        response = installation.wait_for_result()
    if isinstance(response, dict) and not response.get("success", False):
        raise RuntimeError("plugin installation failed: {0}".format(response))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--descriptor", default="code-env/python/desc.json")
    parser.add_argument("--instance-config", required=True)
    parser.add_argument("--plugin-id", required=True)
    parser.add_argument("--plugin-archive", required=True)
    parser.add_argument("--result-file", required=True)
    args = parser.parse_args(argv)

    interpreters = _read_interpreters(args.descriptor)
    url, api_key = _read_target(args.instance_config)
    client = dataikuapi.DSSClient(url, api_key=api_key)
    _install_plugin(client, args.plugin_archive)
    results = verify_plugin_code_environments(client, args.plugin_id, interpreters)

    with open(args.result_file, "w") as result_file:
        json.dump({"results": results}, result_file, indent=2, sort_keys=True)
        result_file.write("\n")

    failures = failed_results(results)
    for result in results:
        status = "PASS" if result["success"] else "FAIL"
        print("{0} {1}: {2}".format(status, result["interpreter"], result["error"] or result["environment_name"]))
    if failures:
        raise SystemExit("{0} Python code environment(s) failed".format(len(failures)))


if __name__ == "__main__":
    main()
