# Knowledge Capture Policy

## Purpose

Ensure durable, high-value knowledge is captured during development without creating noise or duplication.

## Core rule

Only capture knowledge that would be hard, risky, or lossy to reconstruct later from code and tests.

Do not document obvious or low-value information.

## Search before writing

Before adding or updating knowledge artifacts:

- search existing documentation (specs, runbooks, patterns, decisions)
- prefer updating or refining existing content over creating new entries
- avoid duplicating information across artifacts

## When to update knowledge artifacts

At session end, update a knowledge artifact only if the session produced:

- a design decision
- a new or changed invariant
- a repeated failure pattern
- a stable operational procedure
- a necessary spec clarification

If none apply:
- do not update knowledge artifacts

## Artifact ownership

Update the appropriate artifact based on knowledge type:

- patterns → `/agent/patterns.md`
- procedures → `/runbooks/`
- system behavior / contracts → `/specs/`
- design decisions → `/docs/decisions/` (or equivalent)
- execution state → `/status/session_handoff.md` (always)

## Constraints

- keep updates concise and structured
- modify existing artifacts instead of creating new ones when possible
- do not duplicate information across artifacts
- do not write narrative summaries or logs

## Principle

Document what code cannot safely explain later.
