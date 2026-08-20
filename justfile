export DSS_VERSION := env_var_or_default("DSS_VERSION", "14.7.0")
LOG_LEVEL := env_var_or_default("LOG_LEVEL", "INFO")

export EXTRA_DSS_PY_VERSIONS := env_var_or_default("EXTRA_DSS_PY_VERSIONS", "3.8 3.9 3.10 3.11 3.12 3.13 3.14")
export DSS_IMAGE := if EXTRA_DSS_PY_VERSIONS != "" {
    "dataiku/dss:" + DSS_VERSION + "-py-" + replace(EXTRA_DSS_PY_VERSIONS, ' ', '-')
} else {
    "dataiku/dss:" + DSS_VERSION
}

COMPOSE_FILE_BASE := "docker-compose.yaml:docker-compose.observability.yaml"
COMPOSE_FILE := if EXTRA_DSS_PY_VERSIONS != "" {
    COMPOSE_FILE_BASE + ":docker-compose.python.yaml"
} else {
    COMPOSE_FILE_BASE
}

[group('infra')]
[doc('Start containers')]
start:
    #!/bin/sh
    cd {{source_directory()}}
    COMPOSE_FILE={{COMPOSE_FILE}} docker compose up --detach --no-recreate

dev: start
    #!/bin/sh
    cd {{source_directory()}}
    COMPOSE_FILE={{COMPOSE_FILE}} mutagen-compose up --no-recreate

[group('infra')]
[doc('Down containers. Accepts docker compose down flags, e.g. --volumes to also remove volumes')]
stop *FLAGS:
    #!/bin/sh
    cd {{source_directory()}}
    COMPOSE_FILE={{COMPOSE_FILE}} mutagen-compose down --remove-orphans {{FLAGS}}

[group('infra')]
[doc('Run setup profile to setup DSS instance')]
setup: 
    #!/bin/sh
    cd {{source_directory()}}

    if [ -d .env.dss ]; then rm -rf .env.dss; fi
    touch .env.dss
    COMPOSE_FILE={{COMPOSE_FILE}} LOG_LEVEL={{LOG_LEVEL}} COMPOSE_PROFILES=setup docker compose up --attach setup

[group('infra')]
[doc('Run observability profile to start observability stack')]
observe: 
    #!/bin/sh
    cd {{source_directory()}}
    COMPOSE_FILE={{COMPOSE_FILE}} COMPOSE_PROFILES=observability docker compose up --detach

build: start
    #!/bin/sh
    cd {{source_directory()}}
    COMPOSE_FILE={{COMPOSE_FILE}} mutagen-compose up --no-recreate --detach
    COMPOSE_FILE={{COMPOSE_FILE}} LOG_LEVEL={{LOG_LEVEL}} COMPOSE_PROFILES=build docker compose up --attach build --no-recreate

[group('tests')]
[doc('Run the descriptor-driven DSS Python compatibility matrix with host pytest')]
integration-tests:
    #!/bin/sh
    cd {{source_directory()}}
    make integration-tests

[group('infra')]
clean:
    #!/bin/sh
    cd {{source_directory()}}
    COMPOSE_FILE={{COMPOSE_FILE}} COMPOSE_PROFILES=observability,setup,dev,build mutagen-compose down -v
    COMPOSE_FILE={{COMPOSE_FILE}} COMPOSE_PROFILES=observability,setup,dev,build mutagen-compose rm
