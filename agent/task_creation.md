## Task Creation Rules

### Purpose

These rules define how new backlog tasks are created by the planning agent.

They ensure that tasks remain:
- small and executable in one session
- unambiguous
- consistent with architecture and workflow constraints
- stable over time

## 1. Task identity

- Each task must have a unique identifier of the form:

    T-00001, T-00002, ...

- IDs are:
  - globally unique
  - monotonically increasing
  - never reused
  - never renumbered

- The planning agent must:
  - determine the highest existing task ID
  - assign the next available ID

## 2. Task granularity

Each task must:

- be executable within one implementation session
- have a clearly bounded scope
- affect a small, coherent part of the system

A task must not:

- span multiple domains unless strictly necessary
- include multiple unrelated changes
- require implicit follow-up work to be considered complete

## 3. Task structure

Each task must contain the following fields:

- title
- type (implementation | test | documentation | refactor)
- priority (high | medium | low)
- status (open)
- milestone
- blocked_by
- depends_on
- scope
- acceptance_signal
- files_likely_touched
- notes
- discovered_from
- next_if_done
- next_if_blocked

No required field may be omitted.

## 4. Scope definition

The scope must:

- describe exactly what is to be implemented or changed
- reference relevant specs when applicable
- avoid vague language

Good:
- "Implement canonical instrument model with required fields from specs/data_model.md"

Bad:
- "Work on instrument model"

## 5. Acceptance signal

Each task must define a clear acceptance signal.

The acceptance signal must:

- be observable
- be testable or verifiable
- not depend on subjective judgment

Good:
- "Instrument model can represent equity, option, and FX and passes unit tests"

Bad:
- "Instrument model looks correct"

## 6. Dependencies

- `depends_on` lists tasks that must be completed before this task can start
- `blocked_by` lists external blockers (rare)

Rules:

- Do not invent dependencies unnecessarily
- Keep dependency chains shallow
- Prefer sequencing via `next_if_done` over complex dependency graphs

## 7. next_if_done / next_if_blocked

Each task must define:

- `next_if_done`
- `next_if_blocked`

Rules:

- These must point to valid task IDs or explicit actions
- Do not leave them undefined
- Do not create long chains in advance

Typical usage:

- next_if_done → next logical task
- next_if_blocked → investigation or smaller fallback task

## 8. Source attribution

Each task must include:

- `discovered_from`

Valid values include:

- a spec file (e.g. specs/data_model.md)
- a runbook
- a previous task
- a session handoff

This ensures traceability and prevents arbitrary work.

## 9. Anti-duplication

Before creating a new task, the planning agent must:

- search the backlog
- verify that no equivalent task already exists

If a similar task exists:
- refine or extend it instead of duplicating

## 10. Domain alignment

Tasks must align with system architecture:

- must not violate domain boundaries
- must not introduce cross-domain shortcuts
- must respect interface contracts

If a task would violate architecture:
- create a spec/refinement task instead

## 11. Incremental planning

The planning agent must:

- create only the next necessary tasks
- avoid fully pre-planning large milestones
- allow implementation feedback to shape future tasks

Rule of thumb:

- always keep 1–5 ready tasks ahead
- do not create large task batches without need

## 12. File placement

Each task must be stored as:

- one file per task under `/backlog/open/`

Filename format:

    T-00001-short-slug.md

The slug is optional but recommended.

## 13. Stability rules

Once created, a task:

- must not change its ID
- must not be repurposed for a different goal
- may be refined for clarity, but not fundamentally altered

If scope changes significantly:
- create a new task instead

## 14. Completion integrity

A task must not be marked complete unless:

- acceptance signal is satisfied
- validation has been executed
- session handoff reflects the outcome

## 15. Failure handling

If a task cannot be completed:

- record the blocker
- do not expand scope
- create a follow-up task if needed
- update `next_if_blocked` accordingly
