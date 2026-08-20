#!/bin/sh
set -e

# Entry point for the DevX tasks image.
# - `docker run <image> init` launches the interactive initializer
# - Other args delegate to `uv run`

if [ "$1" = "init" ]; then
  shift
  exec uv run python /config/scripts/init.py "$@"
fi

exec uv run "$@"

