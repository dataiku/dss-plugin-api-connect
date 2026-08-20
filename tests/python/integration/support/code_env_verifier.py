"""Generic DSS plugin code-environment verification helpers.

This module deliberately does not know about pytest, Docker, GitHub Actions, or
the plugin descriptor.  It is intended to be moved to dku_plugin_test_utils
once the API has been exercised by this repository.
"""


def _creation_error(creation):
    """Return a useful error from a DSS code-environment creation response."""
    messages = creation.get("messages", {}) if isinstance(creation, dict) else {}
    if not isinstance(messages, dict):
        return None

    error = messages.get("error")
    if error:
        details = messages.get("messages", [])
        if isinstance(details, list):
            for detail in details:
                if isinstance(detail, dict) and detail.get("severity") == "ERROR":
                    return detail.get("message") or str(error)
        return str(error)
    return None


def verify_plugin_code_environments(client, plugin_id, interpreters):
    """Create and verify one plugin environment for every requested interpreter.

    Args:
        client: A dataikuapi.DSSClient-compatible object.
        plugin_id: ID of an already-installed DSS plugin.
        interpreters: Ordered iterable of DSS labels, for example ``PYTHON313``.

    Returns:
        A list of dictionaries, one for each requested interpreter.  Failures
        are recorded instead of raised so callers can report the full matrix.
    """
    results = []
    plugin = client.get_plugin(plugin_id)

    for interpreter in interpreters:
        result = {
            "interpreter": interpreter,
            "success": False,
            "environment_name": None,
            "actual_interpreter": None,
            "error": None,
        }
        try:
            creation = plugin.create_code_env(
                python_interpreter=interpreter
            ).wait_for_result()
            error = _creation_error(creation)
            environment_name = creation.get("envName") if isinstance(creation, dict) else None
            result["environment_name"] = environment_name

            if error:
                result["error"] = error
            elif not environment_name:
                result["error"] = "DSS did not return an environment name"
            else:
                environments = client.list_code_envs()
                environment = next(
                    (
                        candidate
                        for candidate in environments
                        if candidate.get("envName") == environment_name
                    ),
                    None,
                )
                if environment is None:
                    result["error"] = "Created environment was not listed by DSS"
                else:
                    actual = environment.get("pythonInterpreter")
                    result["actual_interpreter"] = actual
                    if actual != interpreter:
                        result["error"] = (
                            "DSS created {0}, expected {1}".format(
                                actual, interpreter
                            )
                        )
                    else:
                        result["success"] = True
        except Exception as error:  # DSS client errors are matrix results.
            result["error"] = str(error)
        results.append(result)

    return results


def failed_results(results):
    """Return failed matrix results without choosing how the caller reports them."""
    return [result for result in results if not result["success"]]
