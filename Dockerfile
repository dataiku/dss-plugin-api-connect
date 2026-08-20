FROM python:3.11
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy local files used to setup user devx environment
ADD pyproject.toml pyproject.toml
ADD tasks/config /config
ADD config-tests /tests
ADD config-observability /observability

ARG PYTHONPATH=
# Copy template files for infra folder
RUN mkdir -p /config/templates/project
ADD docker-compose.yaml docker-compose.observability.yaml docker-compose.python.yaml justfile quickstart.md /config/templates/project/
ADD config /config/templates/project/config
ADD plugins /config/templates/project/plugins
ADD docker /config/templates/project/docker

ENV PYTHONPATH=/config/scripts${PYTHONPATH:+:${PYTHONPATH}}
ADD tasks/devx-entrypoint.sh /usr/local/bin/devx-entrypoint
RUN chmod +x /usr/local/bin/devx-entrypoint && mkdir /local
ENTRYPOINT ["/usr/local/bin/devx-entrypoint"]
