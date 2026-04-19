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
- updated `/backlog/open/` (or, as fallback, `/backlog/fix_plan.md`)

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
- implement only the selected backlog task
- modify only required components
- do not expand scope beyond the task definition

6. Validate

    ./scripts/run_fast_checks.sh

7. Write artifacts
- update `/status/session_handoff.md` (current handoff)
- update `/backlog/open/` (or, as fallback, `/backlog/fix_plan.md`)

## Execution Contract

### Purpose

Defines the authoritative rules for task execution, validation, and persistence.

This section complements (but does not replace):
- workflow loop
- task selection rules
- artifact handling

### Execution discipline

During implementation:

- execute exactly one selected task
- do not expand scope
- do not fix unrelated issues
- record unrelated findings as new backlog tasks

### Validation requirement

After implementation:

    ./scripts/run_fast_checks.sh

- validation must confirm acceptance signal
- failed validation means task is not complete

### Version control policy

After a successful session:

- create exactly one commit per task
- commit must reference the task ID
- do not bundle multiple tasks
- do not commit unvalidated work

If blocked:

- do not commit partial work unless explicitly required
- record state in session handoff

### Determinism requirement

All execution must be:

- reproducible from repository artifacts
- independent of agent interpretation
- explainable post hoc

### Relationship to other rules

- Task selection is defined in `/agent/task_selection.md`
- Task creation is defined in `/agent/task_creation.md`
- Execution flow is defined in the workflow loop above

## Task selection rules

- all work must come from backlog
- do not invent tasks
- one task per session
- refine unclear tasks before implementation

## Planning discipline

Planning must produce implementation tasks that are:
- explicit
- bounded
- verifiable
- ready for deterministic selection

Also:
- Do not create vague or oversized tasks.
- Do not leave dependencies or acceptance criteria implicit.

## Artifact-driven memory model

Persistent state:
- backlog → planning
- handoff → execution continuity
- specs → correctness
- runbooks → procedures
- patterns → learned behavior

Artifacts are the only reliable cross-session memory.
Do not rely on implicit knowledge from previous sessions.

## Session handoff usage

`/status/session_handoff.md` is the current continuity artifact between sessions.

It exists to provide the minimum current state needed for the next agent to continue work correctly under limited context.

### At session start

- read `/status/session_handoff.md` unless it is clearly irrelevant to the selected task
- it is especially relevant when:
  - the selected backlog task references prior work
  - the previous session was incomplete, blocked, or partially finished

- use it to reconstruct:
  - recent relevant changes
  - blockers
  - what was intentionally left unchanged
  - the next recommended task

- validate assumptions from the handoff against code and specs when correctness matters

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
- prefer concise structured statements over long narrative explanations

## Validation rules

Run the smallest sufficient validation set for the current task.

Default:

    ./scripts/run_fast_checks.sh

Escalate validation when:
- changes affect multiple components or boundaries
- correctness risk is high
- behavior is uncertain or not well understood
- the change affects persisted state or data integrity

Also:
- Do not skip validation.
- Do not assume correctness without verification.
- treat failed validation as task not complete

## Failure handling

If blocked:
- stop scope expansion
- record blocker
- recommend next task
- do not workaround silently
- do not attempt large workarounds outside task scope

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

## Post-session verification

After each session, the harness must verify that the session outcome is valid before version-control actions are allowed.

Verification must check:
- required artifacts were updated
- handoff state is complete and consistent
- validation results are present
- task result is well-formed
- blocked or partial outcomes are properly documented

Do not commit or push session results unless post-session verification passes.

## Recovery mode

Recovery mode exists to restore the repository to a previously trusted state when current progress is judged unsound, unstable, or misaligned.

### Recovery trigger

Recovery mode should be considered when:
- repeated failures indicate systemic drift
- architecture boundaries have been violated across sessions
- recent work has degraded correctness, clarity, or milestone progress
- a previously validated state is more trustworthy than the current state

### Ownership

- Implementation agents may detect recovery conditions and recommend recovery mode.
- Implementation agents must not independently execute rollback.
- The planning/recovery agent owns the decision whether recovery mode is required.
- The harness executes rollback and restoration actions deterministically.

### Workflow effect

When recovery mode is the safer option:
- stop forward implementation work
- record the recovery reason
- switch to planning/recovery work
- do not continue patching the current line of development

### Artifact requirements

Recovery decisions and results must be recorded in:
- `/status/session_handoff.md`
- `/backlog/open/` (or, as a fallback, in `/backlog/fix_plan.md`)

The repository must clearly state:
- why recovery was needed
- what state was restored
- what the next recommended task is

## Task creation governance

When operating in planning mode, the agent must follow:

    /agent/task_creation.md

as the authoritative specification for creating and updating backlog tasks.

The agent must:

- apply all task creation rules defined in that document
- not invent alternative task formats or structures
- not omit required fields
- not violate task identity, granularity, or dependency rules

If a conflict exists between:
- `agent/task_creation.md`
- other artifacts

then:

- the agent must not proceed with task creation
- the conflict must be recorded in `/backlog/fix_plan.md`
- a clarification task must be created

The `agent/task_creation.md` document is considered normative for:
- task structure
- task identity
- backlog evolution rules

## Task selection governance

When selecting a task for implementation, the agent must follow:

    /agent/task_selection.md

as the authoritative specification for task selection.

The agent must:

- select exactly one task
- not invent tasks
- not modify task scope during selection
- not skip higher-priority tasks without explicit reason

If no valid task exists:

- switch to planning mode
- update the backlog accordingly

If multiple tasks appear equally valid:

- resolve using deterministic tie-breaking rules defined in `/agent/task_selection.md`

Task selection must be:

- deterministic
- reproducible
- explainable from repository artifacts alone
