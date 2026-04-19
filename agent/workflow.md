# Workflow Rules

## Purpose

This file defines the general agent workflow and execution discipline.

It specifies:
- how tasks are selected and executed
- how context is loaded and used
- how artifacts are written and updated
- how failures and validation are handled

These rules are project-agnostic and reusable across repositories.

They must be followed for every session unless explicitly overridden by higher-priority instructions.

## Operating modes

### Implementation mode
- exactly one backlog item
- no scope expansion
- minimal context loading
- targeted validation

### Planning mode
Used when:
- no valid task exists
- backlog is unclear
- blocked by missing decisions

Output:
- updated `/backlog/fix_plan.md`

Do not mix modes.

## Workflow loop

1. Initialize environment

    ./scripts/session_init.sh
    ./scripts/verify_env.sh

2. Select task
- one task from backlog
- highest-priority non-blocked

3. Load minimal context
- AGENT.md
- one backlog item
- 1–3 specs
- one runbook
- touched files only

4. Search before acting
- do not assume missing implementation

5. Execute
- minimal scoped change only

6. Validate

    ./scripts/run_fast_checks.sh

7. Write artifacts
- update `/status/session_handoff.md` (current handoff)
- update `/backlog/fix_plan.md`

## Task selection rules

- all work must come from backlog
- do not invent tasks
- one task per session
- refine unclear tasks before implementation

## Artifact-driven memory model

Persistent state:
- backlog → planning
- handoff → execution continuity
- specs → correctness
- runbooks → procedures
- patterns → learned behavior

## Session handoff usage

`/status/session_handoff.md` is the current continuity artifact between sessions.

It exists to provide the minimum current state needed for the next agent to continue work correctly under limited context.

### At session start
- read `/status/session_handoff.md` when:
  - the selected backlog task references prior work, or
  - the previous session was incomplete, blocked, or partially finished
- use it to reconstruct:
  - recent relevant changes
  - blockers
  - what was intentionally left unchanged
  - the next recommended task

### During the session
- treat `/status/session_handoff.md` as read-only context
- do not append running notes or incremental logs to it

### At session end
- overwrite `/status/session_handoff.md` with the latest relevant handoff state
- keep only current actionable information
- remove obsolete or superseded details

### Scope rules
- keep the file concise and focused
- do not use it as a backlog replacement
- do not duplicate spec content unless needed for immediate continuation
- prefer structured statements over narrative summaries

### History handling
- `/status/session_handoff.md` is the current handoff only
- if older handoffs need to be preserved, store them in `/status/handoff_history/`
- do not turn the current handoff into an append-only history log

The goal is fast and accurate reconstruction of development state for the next session, not historical completeness.

## Artifact-writing rules

Artifacts must optimize for:
- fast reconstruction of state
- minimal ambiguity
- structured clarity

When writing:
- distinguish facts / decisions / blockers / next steps
- state what changed and what did not
- avoid vague wording
- do not rely on prior session memory

## Validation rules

Run the smallest sufficient validation set for the current task.

Default:

    ./scripts/run_fast_checks.sh

Escalate validation when:
- changes affect multiple components or boundaries
- correctness risk is high
- behavior is uncertain or not well understood
- the change affects persisted state or data integrity

Do not skip validation.
Do not assume correctness without verification.

## Failure handling

If blocked:
- stop scope expansion
- record blocker
- recommend next task
- do not workaround silently

## Continuous improvement

If a failure pattern repeats:
- update `/agent/patterns.md`
- encode prevention as reusable guidance
- do not rely on memory

## Anti-drift rules

- do not optimize outside scope
- do not refactor unrelated code
- do not add unnecessary abstractions
- do not assume intent beyond artifacts
