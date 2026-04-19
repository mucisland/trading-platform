# Agent Session Runbook

## Purpose

This runbook defines how to execute a single agent session using the harness.

It applies to both:
- implementation sessions
- planning sessions

## Overview

Each session:

1. initializes the environment
2. selects or receives a task (implementation mode)
3. loads minimal context
4. generates a prompt
5. optionally invokes an agent
6. produces updated repository artifacts

Sessions are:
- bounded (one task per session)
- stateless (continuity via artifacts)
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

- overrides automatic selection

### Planning mode

    --mode planning

- updates backlog and planning state
- ensures backlog satisfies selection contract
- evaluates whether recovery mode is needed

Optional:

    --planning-goal "<text>"

## Context inputs

The harness always loads:

- AGENT.md
- agent/workflow.md
- agent/project_rules.md
- agent/patterns.md
- backlog
- session_handoff.md

Optional inputs:

    --spec <file>
    --runbook <file>
    --file <file>

These are injected into the prompt as structured context.

## Task selection

### Task sources

Tasks are loaded in this order:

1. `/backlog/open/*.md` (preferred)
2. fallback: `/backlog/fix_plan.md`

### Selection rules

The selector chooses a task that is:

- status = open
- not blocked (`blocked_by` empty)
- dependencies satisfied
- has an `acceptance_signal`
- has defined `scope`

Tasks are ranked by:

1. priority (high → medium → low)
2. milestone
3. task id

### If no task is selectable

- implementation mode fails
- switch to planning mode to repair backlog

## Outputs

The harness writes:

- `.artifacts/current_session_prompt.txt`
- `.artifacts/current_session_manifest.json`

## Agent invocation

By default:
- only the prompt is generated

To invoke an agent directly:

    --invoke --agent claude-code
    --invoke --agent codex

Example:

    python scripts/run_agent_session.py \
        --mode implementation \
        --invoke --agent claude-code

## Recovery mode

Planning sessions evaluate whether recovery is required.

Recovery means:
- restoring a previous known-good repository state
- stopping forward implementation work

### Forcing recovery evaluation

    --force-recovery

This injects an explicit recovery instruction into the planning prompt.

### Recovery ownership

- Implementation agents may recommend recovery
- Planning agent decides if recovery is required
- Harness executes rollback (future extension)
- Recovery must be recorded in:
  - session_handoff.md
  - backlog

## Expected agent behavior

Agents must:

- follow AGENT.md and workflow rules
- operate within one session and one task
- update:
  - `/status/session_handoff.md`
  - `/backlog/fix_plan.md` (if needed)
- keep changes minimal and scoped
- run validation
- respect version control policy

## Failure handling

If any of the following occurs:

- no selectable task
- environment setup failure
- script failure
- prompt generation failure

Then:

- stop execution
- switch to planning or environment repair tasks

## Post-session verification

After the agent finishes, run:

    python scripts/verify_session_outcome.py

This verifies that:
- `status/session_handoff.md` was updated
- required session artifacts exist
- validation results are recorded
- task result is valid
- blocked or partial sessions are documented correctly

Verification writes:

    .artifacts/current_session_verification.json

Do not commit or push session changes unless verification passes.

## Finalizing a session

After post-session verification passes, finalize the session with:

    python scripts/finalize_session.py

This will:
- read the current session manifest
- read the current session handoff
- generate a structured commit message
- create exactly one commit for the session

To also push the commit:

    python scripts/finalize_session.py --push

Planning sessions are not committed by default.
To allow a planning-session commit:

    python scripts/finalize_session.py --allow-planning-commit

Do not finalize a session unless post-session verification has passed.

## Core principle

Each session must produce:

- a clear and minimal state transition
- updated repository artifacts
- a valid next step

The system must remain:
- deterministic
- observable
- restartable at all times
