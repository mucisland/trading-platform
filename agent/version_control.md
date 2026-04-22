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

Each session produces at most one commit.

A commit represents one completed task or one recovery event and must reflect a coherent repository state.

### Scope

- A commit must correspond to exactly one task or one recovery event.
- Do not split one task across multiple commits.
- Do not combine multiple tasks into one commit.
- Do not include changes unrelated to the selected task.

### Inclusion

- Usually, all files changed, added, or removed during a session that are not excluded by `.gitignore` must be included in the commit.

Exceptions:
- files unrelated to the selected task must not be included
- ephemeral session artifacts must not be included
- files explicitly excluded by workflow policy must not be included

### State integrity

- The repository must be in a consistent state at commit time.
- Commits must not introduce broken or unusable states.

### Incomplete work

- Do not commit partial or incomplete implementation work.
- Blocked or incomplete sessions must not produce a commit.

### Commit message

- Must include a task ID or recovery ID.
- Must concisely describe the change.

### Principle

A commit is the atomic, durable representation of one completed unit of work.
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

Version control history must remain:

- linear
- traceable
- consistent with repository state

Do not:

- rewrite history
- amend past commits
- squash commits
- force push

Exception:

- controlled recovery execution may restore a previous repository state, but must be recorded as a new recovery commit.

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

Recovery must be explicitly recorded in version control.

Each recovery execution produces exactly one recovery commit.

### Scope

- A recovery commit represents one recovery event.
- It must not include unrelated changes.
- It must not reintroduce reverted implementation code.

### Content

A recovery commit must include:

- the recovery history entry (`/status/recovery_history/`)
- the updated session handoff
- any required backlog updates

### Commit message

- Must include the recovery ID.
- Must identify the restored target state.
- Must concisely describe the recovery action.

### Principle

A recovery commit is the durable record that the repository was intentionally restored to a previous trusted state.

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
