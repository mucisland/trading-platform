# Task Selection Rules

## Purpose

This document defines how an agent selects the next task to execute.

The goal is deterministic, reproducible task selection.

## 1. Input set

The agent must consider:

- all tasks in `/backlog/open/`
- current `/status/session_handoff.md` (if relevant)

Closed or completed tasks must not be considered.

## 2. Eligibility filter

A task is eligible if:

- status = open
- all `depends_on` tasks are completed
- no blocking condition prevents execution

If a task is blocked:
- it must not be selected

## 3. Priority ordering

Eligible tasks are ordered by:

1. priority (high > medium > low)
2. milestone (earlier milestone preferred)
3. creation order (lower task ID first)

This ordering must be strictly applied.

## 4. Milestone rule

The agent must:

- prefer tasks from the current active milestone
- not jump ahead unless:
  - current milestone has no eligible tasks

## 5. next_if_done preference

If the previous session completed a task and:

- `next_if_done` points to a valid eligible task

then:

- that task must be selected

This rule overrides general priority ordering.

## 6. next_if_blocked preference

If the previous task was blocked and:

- `next_if_blocked` points to a valid eligible task

then:

- that task must be selected

## 7. Single-task rule

The agent must:

- select exactly one task
- not batch tasks
- not combine tasks

## 8. No task invention

The agent must not:

- create a new task during selection
- modify task scope to fit selection

If no suitable task exists:

- switch to planning mode

## 9. Determinism requirement

Given the same repository state:

- the same task must always be selected

No randomness or subjective judgment is allowed.

## 10. Tie-breaking

If multiple tasks are still equal after ordering:

- select the task with the lowest ID

## 11. Failure handling

If the agent cannot determine a valid task:

- record the issue
- switch to planning mode
- create clarification or refinement tasks

## 12. Observability

The agent must be able to explain:

- why the selected task was chosen
- which rules were applied

This explanation must be derivable from artifacts.
