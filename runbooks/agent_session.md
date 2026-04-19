# Agent Session Runbook

## Purpose

This runbook defines how to execute a single agent session using the harness.

It applies to both:
- implementation sessions
- planning sessions

## Overview

Each session:

1. initializes the environment
2. selects or receives a task
3. loads minimal context
4. generates a prompt
5. optionally invokes an agent
6. produces updated repository artifacts

Sessions are:
- bounded
- stateless (via artifacts)
- restartable

## Command

Run:

    python scripts/run_agent_session.py --mode <mode> [options]

## Modes

### Implementation mode

    --mode implementation

- selects one task from backlog
- generates an implementation prompt
- enforces one-task-per-session

Optional:

    --task FP-001

Overrides automatic selection.

### Planning mode

    --mode planning

- updates backlog and planning state
- may decide recovery mode

Optional:

    --planning-goal "<text>"

## Context inputs

By default:

- AGENT.md
- agent/workflow.md
- agent/project_rules.md
- agent/patterns.md
- backlog
- session_handoff

Optional:

    --spec <file>
    --runbook <file>
    --file <file>

## Task selection

In implementation mode:

- tasks are loaded from:
  - `/backlog/open/*.md` (preferred)
  - fallback: `fix_plan.md`
- selection is deterministic:
  - open
  - not blocked
  - dependencies satisfied
  - acceptance_signal defined
  - smallest priority value wins

If no task is selectable:
- switch to planning mode

## Outputs

The harness writes:

- `.artifacts/current_session_prompt.txt`
- `.artifacts/current_session_manifest.json`

## Agent invocation

To invoke directly:

    --invoke --agent claude-code
    --invoke --agent codex

Otherwise:
- prompt is generated for manual use

## Recovery mode

Planning sessions evaluate whether recovery is required.

You can force recovery evaluation:

    --force-recovery

Recovery decisions:
- are made by the planning agent
- executed by the harness (future step)
- recorded in:
  - session_handoff.md
  - backlog

## Expected agent behavior

Agents must:

- follow AGENT.md and workflow rules
- update:
  - session_handoff.md
  - backlog (if needed)
- keep changes small and scoped
- respect version control policy

## Failure handling

If:

- no task is selectable
- environment fails
- prompt generation fails

Then:

- stop execution
- fix via planning or environment tasks

## Core principle

Each session must produce:

- a clear state transition
- updated artifacts
- a valid next step

The system must remain restartable at all times.
