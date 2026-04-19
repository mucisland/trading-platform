# Tooling Decisions

## Purpose

This document records the foundational tooling choices for the repository.

These decisions are fixed early so that:
- implementation agents do not invent inconsistent tooling
- environment setup is reproducible
- validation remains fast and deterministic
- session behavior stays consistent over time

## Chosen baseline

The repository uses:

- `src/` layout for Python package structure
- Python `>=3.12`
- `uv` for dependency and environment management
- `uv` build backend
- `ruff` for linting and formatting
- `ty` for static type checking
- `pytest` for testing

The following may be added later, but are not part of the initial baseline:

- `coverage.py` for coverage reporting
- `pre-commit` for local hook enforcement

## Rationale

These choices are intended to minimize:
- tool sprawl
- configuration drift
- slow validation loops
- ambiguity for implementation agents

They are also intended to support:
- fast session startup
- small deterministic validation steps
- consistent project structure

## Workflow implications

Implementation and planning agents must not introduce alternative tools for:
- formatting
- linting
- type checking
- testing

Any change to the baseline toolchain must be recorded explicitly in repository artifacts before implementation.
