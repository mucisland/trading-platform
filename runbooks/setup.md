# Setup Runbook

## Purpose

This runbook defines the canonical environment setup path for all agent and human development sessions.

It ensures:
- consistent environment initialization
- reproducible execution conditions
- safe restart of development sessions

## Script roles

### ./scripts/bootstrap.sh

Use only for:
- fresh machines
- fresh containers
- CI environments

Responsibilities:
- verify required system tools are available
- create local virtual environment if missing
- install pinned dependencies
- prepare required local directories
- prepare config templates if missing

Do not use during normal implementation sessions.

### ./scripts/session_init.sh

Use at the start of every session.

Responsibilities:
- detect repository root
- ensure local environment exists
- ensure dependencies are available
- ensure required local directories exist
- ensure required config templates exist
- perform only lightweight, non-destructive setup
- exit quickly if already ready

This script prepares the environment but does not guarantee correctness.

### ./scripts/verify_env.sh

Use after session_init.sh and before implementation work.

Responsibilities:
- verify Python/toolchain availability
- verify virtual environment availability
- verify dependency import sanity
- verify required paths/config files exist
- verify required local services are reachable when needed

This script is the authoritative check that the environment is valid.

### ./scripts/start_local_services.sh

Use only for tasks that require local infrastructure.

Responsibilities:
- start local services
- wait for readiness
- print connection summary

### ./scripts/stop_local_services.sh

Stops local infrastructure started for development.

### ./scripts/run_fast_checks.sh

Runs the default fast validation lane.

Responsibilities:
- formatting check
- linting
- type checking
- smoke/unit subset

## Canonical session start

    ./scripts/session_init.sh
    ./scripts/verify_env.sh

If the task requires local services:

    ./scripts/start_local_services.sh

## Success criteria

The environment is considered valid only if:
- verify_env.sh completes successfully
- no required tools or dependencies are missing
- required config files and directories exist
- required services (if needed) are reachable

Do not proceed with implementation work unless these conditions are met.

## Failure handling

If session_init.sh fails:
- stop the session
- record the failure in session_handoff.md
- recommend an environment-fix task

If verify_env.sh fails:
- do not proceed with implementation
- treat this as a blocking issue
- record the failure
- switch to fixing the environment

Do not partially proceed in a degraded environment.

## Execution discipline

- always run session_init.sh at the start of a session
- always run verify_env.sh before implementation
- do not skip verification
- do not assume environment correctness
- rerun verification if environment changes during the session

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
- opaque migrations with broad side effects
- prompts requiring operator input
