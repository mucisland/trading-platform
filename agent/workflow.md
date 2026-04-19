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
- updated `/backlog/open/` (or fallback `/backlog/fix_plan.md`)

Do not mix modes.

## Workflow loop

1. Initialize environment

    ./scripts/session_init.sh
    ./scripts/verify_env.sh

2. Select task
- must follow `/agent/task_selection.md`

3. Load minimal context
- AGENT.md
- one backlog item
- 1–3 relevant specs
- one runbook
- touched files only

4. Search before acting
- do not assume missing implementation

5. Execute
- implement only the selected backlog task
- modify only required components
- do not expand scope

6. Validate

    ./scripts/run_fast_checks.sh

7. Write artifacts
- update `/status/session_handoff.md`
- update `/backlog/open/` (or fallback `/backlog/fix_plan.md`)

## Execution Contract

### Purpose

Defines the authoritative rules for execution, validation, and persistence.

### Execution discipline

- execute exactly one task
- do not expand scope
- do not fix unrelated issues
- record unrelated findings as new tasks

### Validation requirement

After implementation:

    ./scripts/run_fast_checks.sh

- acceptance signal must be satisfied
- failed validation = task not complete

### Version control policy

After a successful session:

- exactly one commit per task
- commit must reference task ID
- do not bundle multiple tasks
- do not commit unvalidated work

If blocked:
- do not commit partial work (unless explicitly required)
- record state in handoff

### Determinism requirement

All execution must be:

- reproducible from repository artifacts
- independent of agent interpretation
- explainable post hoc

## Task selection governance

Task selection is governed by:

    /agent/task_selection.md

The agent must:

- select exactly one task
- not invent tasks
- not modify task scope
- not skip higher-priority tasks without reason

If no valid task exists:
- switch to planning mode

Task selection must be:

- deterministic
- reproducible
- explainable

## Task creation governance

Planning must follow:

    /agent/task_creation.md

The agent must:

- use the defined task structure
- assign valid unique IDs
- ensure tasks are small, explicit, and testable
- avoid duplication

If conflicts exist:
- do not proceed
- record in backlog
- create clarification task

## Planning discipline

Planning must produce tasks that are:

- explicit
- bounded
- verifiable
- ready for deterministic selection

Do not:
- create vague tasks
- create oversized tasks
- leave dependencies implicit

## Artifact-driven memory model

Persistent state:

- backlog → planning
- handoff → execution continuity
- specs → correctness
- runbooks → procedures
- patterns → learned behavior

Artifacts are the only reliable cross-session memory.
Do not rely on implicit knowledge.

## Session handoff usage

`/status/session_handoff.md` is the current continuity artifact.

### At session start

- read handoff unless clearly irrelevant
- especially when:
  - task references prior work
  - previous session was incomplete

Use it to reconstruct:
- recent changes
- blockers
- intentional gaps
- next task

Validate assumptions against code when necessary.

### During the session

- treat handoff as read-only
- do not append logs

### At session end

- overwrite with current state
- keep concise and actionable
- remove obsolete information

### Scope rules

- do not use as backlog
- do not duplicate specs
- prefer structured statements

### History handling

- store history in `/status/handoff_history/`
- do not append to current handoff

## Artifact-writing rules

Artifacts must optimize for:

- fast reconstruction
- clarity
- minimal ambiguity

When writing:

- distinguish facts / decisions / blockers / next steps
- state what changed and what did not
- avoid vague wording
- do not rely on prior sessions

## Validation rules

Run minimal sufficient validation:

    ./scripts/run_fast_checks.sh

Escalate when:
- cross-domain changes
- correctness risk is high
- behavior is unclear
- persistence is affected

Also:

- do not skip validation
- do not assume correctness
- failed validation = incomplete task

## Failure handling

If blocked:

- stop execution
- do not expand scope
- record blocker
- recommend next task
- do not workaround silently

## Post-session verification

The harness must verify:

- artifacts updated
- handoff complete
- validation results present
- task result well-formed

Do not commit unless verification passes.

## Recovery mode

### Purpose

Restore repository to a trusted state when progress is unsound.

### Trigger

Consider recovery when:

- repeated failures occur
- architecture boundaries are violated
- correctness degrades
- previous state is more trustworthy

### Ownership

- implementation agents may recommend recovery
- planning/recovery agent decides
- harness executes rollback

### Workflow effect

- stop forward work
- record reason
- switch to recovery planning

### Artifact requirements

Record in:

- `/status/session_handoff.md`
- backlog

Must include:

- reason
- restored state
- next task

## Continuous improvement

If patterns repeat:

- update `/agent/patterns.md`
- encode prevention

Do not rely on memory.

## Anti-drift rules

- do not optimize outside scope
- do not refactor unrelated code
- do not add unnecessary abstractions
- do not assume intent beyond artifacts
