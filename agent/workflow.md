# Workflow Rules

## Purpose
- define general agent workflow and execution discipline
- define how sessions are run
- define how artifacts are used as memory
- delegate detailed mechanics to specialized files

## Operating modes
Do not mix modes.

### Implementation mode
- complete one task from backlog
- no scope expansion
- targeted validation

### Planning mode
- used when no valid task exists or backlog is unclear
- outputs backlog updates

### Recovery mode
- used to restore repository to a previously trusted state when current progress is unsound
- consider recovery when:
    - repeated failures indicate drift
    - architecture boundaries are violated
    - correctness degrades
    - a previous state is more trustworthy
- implementation agents may recomment recovery (via session artifact)
- planning/recovery agent decides for or against entering recovery
- planning/recovery agent produces recovcery plan artifact
- harness executes recovery deterministically:
    - restore the selected state
    - run required validation
    - create a recovery history entry
    - update session handoff
    - create a recovery commit

## Workflow loop
1. initialize environment
2. select task or planning goal
3. load minimal context
4. search before acting
5. execute scoped change
6. validate
7. update artifacts

## Harness rejection handling

If the harness rejects a workflow step, the current execution path must stop.

The rejection must be converted into explicit repository state by:

- recording the failure in durable artifacts
    - machine-readable: `.session-artifacts/current_blocker.json`
    - history: `status/blockers/B-xxxxx.md`
- updating the current session handoff
- creating or updating the next recommended task

A harness rejection does not permit silent retry or scope expansion.

When possible, the workflow must continue through:
- planning mode
- a repair task
- or explicit escalation

## Task selection governance
- task selection is governed by `/agent/task_selection.md`
- implementation agents must follow it
- if no valid task exists, switch to planning mode

## Task creation governance
- planning agents must follow `/agent/task_creation.md`
- tasks must be explicit, bounded, and selector-ready

## Artifact-driven memory model
- backlog → planning
- handoff → execution continuity
- specs → correctness
- runbooks → procedures
- patterns → learned behavior

Artifacts are the only reliable cross-session memory.

## Artifact-writing rules

Artifacts must optimize for:

- fast reconstruction
- clarity
- minimal ambiguity

When writing:

- do not rely on prior sessions

## Session handoff usage

### At session start
- read current handoff unless clearly irrelevant
- use it to reconstruct recent changes, blockers, intentional gaps, and next task
- validate assumptions when correctness matters

### During the session
- treat handoff as read-only context

### At session end
- overwrite with current actionable state
- do not append logs
- keep history separate

## Validation rules
- run the smallest sufficient validation
- default: `./scripts/run_fast_checks.sh`
- do not skip validation
- failed validation means task is incomplete
- detailed validation escalation rules belong in project-specific docs if needed

## Failure handling
If blocked:
- stop execution
- do not expand scope
- record blocker
- recommend next task

## Anti-drift rules
- do not optimize outside scope
- do not refactor unrelated code
- do not add unnecessary abstractions
- do not assume intent beyond artifacts

## Continuous improvement
- recurring issues must be recorded in `/agent/patterns.md`

## Delegated policies
Detailed rules are defined in:
- `/agent/task_selection.md`
- `/agent/task_creation.md`
- `/agent/version_control.md`
- `/runbooks/setup.md`
- `/runbooks/agent_session.md`
- `/runbooks/recovery.md`
