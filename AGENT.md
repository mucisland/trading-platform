# AGENT.md

## Purpose

This repository is developed through a harness-first workflow using a sequence of bounded development sessions.

In each session, one agent works on exactly one scoped task so that context stays small, execution remains controlled, and progress is restartable across sessions.

The repository is the system of record for:
- architecture
- backlog and planning
- handoff state
- runbooks
- implementation status

Also:
- Repository artifacts carry continuity between sessions.
- Chat history is not authoritative.

## Instruction hierarchy

Follow instructions in this order:

1. This file (`AGENT.md`)
2. `/agent/workflow.md` (general workflow rules)
3. `/agent/project_rules.md` (project-specific constraints)
4. `/agent/patterns.md` (learned patterns and failure prevention)
5. `/specs/*.md` (domain definitions)
6. `/runbooks/*.md` (procedures)

If rules conflict:
- project_rules override workflow rules
- workflow rules override general assumptions

## Required startup sequence

At the start of every session:

    ./scripts/session_init.sh
    ./scripts/verify_env.sh

Then:
- select exactly one task from `/backlog/fix_plan.md`
- follow `/agent/workflow.md`

## Core constraints

- all implementation work must originate from the backlog
- exactly one scoped task per session
- do not expand scope implicitly
- artifacts are the only persistent memory between sessions

## Project invariants

Project-specific constraints are defined in:

    /agent/project_rules.md

These must not be violated.

## Continuous improvement

Patterns and recurring issues must be recorded in:

    /agent/patterns.md

Do not rely on remembering past failures.

## Failure rule

If blocked:
- stop work
- record blocker
- recommend next smallest task

## Core principle

The agent is not trusted to:
- remember context
- infer missing design
- expand scope safely

The system is designed so that:
- artifacts define reality
- the harness enforces discipline
- each session is small, verifiable, and restartable
