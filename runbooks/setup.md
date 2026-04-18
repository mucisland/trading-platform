# Setup Runbook

## Purpose
This runbook defines the canonical environment setup path for all agent and human development sessions.

## Script roles

### `./scripts/bootstrap.sh`
Use for fresh machines, fresh containers, or CI workers.

Expected responsibilities:
- verify required system tools are available
- create local virtual environment if missing
- install pinned dependencies
- prepare required local directories
- prepare config templates if missing

### `./scripts/session_init.sh`
Use at the start of every session.

Expected responsibilities:
- detect repository root
- ensure local environment exists
- ensure dependencies are available
- ensure required local directories exist
- ensure required config templates exist
- perform only lightweight, non-destructive setup
- exit quickly if already ready

### `./scripts/verify_env.sh`
Use after `session_init.sh` and before implementation work when environment confidence matters.

Expected responsibilities:
- verify Python/toolchain availability
- verify virtual environment availability
- verify dependency import sanity
- verify required paths/config files exist
- verify required local services are reachable when needed

### `./scripts/start_local_services.sh`
Use only for tasks that require local infrastructure.

Expected responsibilities:
- start local services
- wait for readiness
- print connection summary

### `./scripts/stop_local_services.sh`
Stops local infrastructure started for development.

### `./scripts/run_fast_checks.sh`
Runs the default fast validation lane.

Expected responsibilities:
- formatting check
- linting
- type checking
- smoke/unit subset

## Canonical session start
```
./scripts/session_init.sh
./scripts/verify_env.sh
```

If the task requires local services:
```
./scripts/start_local_services.sh
```

## Requirements for all setup scripts
- non-interactive
- idempotent
- safe to rerun
- explicit failures
- minimal hidden side effects

## Anti-patterns
Do not put these inside generic setup scripts:
- full test suites
- destructive resets
- strategy-specific setup
- vopaque migrations with broad side effects
- prompts requiring operator input
