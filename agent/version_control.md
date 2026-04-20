# Version Control Policy

## Purpose

This document defines how agents must interact with version control.

It ensures that:
- repository history reflects task-level progress
- changes are traceable to backlog tasks
- rollback and recovery remain safe and deterministic

## Core principle

One task → one commit → one coherent change.

Version control history must mirror the logical progression of tasks.

## Commit rules

After a successful implementation session:

- create exactly one commit
- the commit must correspond to exactly one task
- the commit must include all changes required for that task
- the commit must not include unrelated changes

Do not:

- split one task across multiple commits
- combine multiple tasks into a single commit
- commit partial or incomplete work

## Commit preconditions

A commit is allowed only if:

- the task acceptance signal is satisfied
- validation has been executed
- validation has passed
- required artifacts are updated:
  - `/status/session_handoff.md`
  - backlog (if needed)

If these conditions are not met:
- do not commit

## Commit message format

- follow the conventional commits specification (https://www.conventionalcommits.org)
- append the task ID (in paranthesis) to the description
- concisely describe what the change does
- do not include unrelated information
- extend the commit message with a body if needed, e.g. the reason for recovery in a recovery commit

Example:

    chore: initialize src-based project structure (T-00001)

## Blocked tasks

If a task is blocked:

- do not commit partial implementation
- record the state in `/status/session_handoff.md`
- update backlog with:
  - blocker description
  - next steps

## Repository state integrity

- the repository must always be in a consistent, runnable state
- commits must not break:
  - import structure
  - basic validation checks
- Agents must not leave the repository in a broken intermediate state.

## Branching model

Default:

- work on a single main branch

Do not:

- create feature branches
- create long-lived branches
- introduce merge complexity

## Push policy

After a successful commit:

- push changes to the remote repository

Do not:

- delay pushing completed work
- keep unpushed local changes across sessions

## History integrity

Agents must treat repository history as authoritative.

Do not:

- rewrite history
- amend past commits
- squash commits
- force push

Exception:

- history modification is allowed only in controlled recovery mode executed by the harness

## Recovery interaction

Recovery decisions are owned by the planning/recovery agent.

The planning/recovery agent is responsible for:
- deciding whether recovery mode is required
- selecting the rollback target
- recording the recovery plan in repository artifacts

Implementation agents must not:
- decide rollback scope
- execute rollback independently

The harness is responsible for:
- consuming the recovery plan artifact
- restoring the selected previous state deterministically
- validating the restored state
- recording the recovery result

## Recovery commits

Recovery is a first-class workflow event and must be recorded explicitly in version control.

After a recovery is executed:

- create exactly one recovery commit
- the commit must:
  - reference the recovery ID (R-xxxxx)
  - describe the rollback target
  - include the recovery reason
  - reference validation results
  - state the next recommended task

The recovery commit must include only:

- recovery history entry
- updated session handoff
- required backlog updates

Do not:

- reintroduce reverted implementation code
- modify unrelated files

## Recovery history integrity

Recovery must be persisted across:

- Git history (recovery commit)
- recovery history artifacts (`/status/recovery_history/`)
- session handoff

All three must be consistent.

## Rollback execution constraint

Implementation agents must not:

- perform rollback directly
- revert commits manually

Recovery execution must be:

- initiated by a recovery plan artifact
- executed by the harness deterministically

## Traceability requirement

Each commit must be traceable to:

- a backlog task
- a session handoff
- validation results

This ensures:

- debuggability
- reproducibility
- safe recovery

## Minimalism principle

Version control must remain:

- simple
- linear
- easy to reason about

Avoid introducing:

- complex workflows
- branching strategies
- multi-step commit sequences

Unless explicitly required by future planning decisions.
