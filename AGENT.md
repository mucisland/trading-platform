# AGENT.md

## Purpose
This repository is developed through a harness-first workflow with one scoped task per session.

The repository is the system of record for:
- architecture
- backlog and planning
- handoff state
- runbooks
- implementation status

Chat history is not authoritative.

## Architectural priorities
Always optimize in this order unless an explicit architecture decision says otherwise:
1. restartability
2. simplicity
3. observability
4. safety / loss prevention
5. extensibility

When priorities conflict, prefer the higher-ranked priority unless the repository contains an explicit recorded decision authorizing a different tradeoff.

## Core workflow rules
- perform exactly one scoped task per session
- a scoped task should normally change only one architectural seam or one backlog item
- do not combine multiple subsystem changes in one session unless the task is explicitly defined as a wiring task
- search the codebase before assuming missing implementation
- do not broaden scope implicitly
- if unrelated issues are discovered, record them in backlog instead of fixing them unless they block the current task
- update handoff and backlog artifacts at the end of every session
- prefer modifying existing abstractions over creating parallel ones
- do not start implementation work without a named backlog item or explicitly recorded task in `/backlog/fix_plan.md`
- if no suitable task exists, switch to planning mode and update the backlog instead of improvising implementation work
- select exactly one task from `/backlog/fix_plan.md` before starting work
- do not invent new implementation tasks outside the backlog
- if no suitable task exists, switch to planning mode and update `/backlog/fix_plan.md` instead of starting implementation
- when multiple tasks are available, prefer the highest-priority non-blocked task
- if a task is ambiguous or underspecified, refine it in the backlog before implementation
- do not modify multiple backlog items in a single session
- if new work is discovered, record it as a new backlog item instead of expanding the current task

## Environment setup rules
At the start of every session run:

    ./scripts/session_init.sh
    ./scripts/verify_env.sh

If the current task needs local infrastructure, also run:

    ./scripts/start_local_services.sh

Do not invent ad hoc setup when scripted setup exists.
Do not silently work around environment failures.

If `session_init.sh` or `verify_env.sh` fails, do not continue with implementation work unless the current scoped task is specifically to fix environment setup.
Record blocking setup failures in `/status/session_handoff.md` and `/backlog/fix_plan.md`.

## Boundary preservation rules
- strategy code must never talk directly to venue adapters
- strategy code must never emit executable orders directly
- trader-local risk must never bypass global risk
- execution must never make strategy decisions
- ledger/recovery remains authoritative for recoverable truth
- runtime control governs readiness and automatic resume
- correctness must not depend on graceful shutdown
- correctness-critical streams must be durably captured
- trader runtime is homogeneous and permanently bound to one strategy configuration
- live semantics are primary; backtest and paper trading should share core semantics wherever possible
- trader code must not access other traders’ internal state
- trader code may consume only its allowed event/account context
- do not invent implicit global netting or trader-conflict resolution unless a recorded architecture decision requires it
- do not introduce correctness dependencies on in-memory-only state without a recorded recovery contract
- trader recovery must use the standard snapshot/replay contract
- replay catch-up must complete before live rejoin unless a recorded architecture decision says otherwise

## Session context discipline
Load only:
- this file
- one backlog item
- 1–3 relevant spec files
- one relevant runbook
- the touched source/test files
- compact prior handoff only if needed

Do not load unrelated specs, full logs, or broad repo context by default.

## Validation rules
Run the smallest sufficient validation set for the current task.

Default fast lane:

    ./scripts/run_fast_checks.sh

Escalate when the task touches:
- recovery
- cross-domain boundaries
- execution behavior
- multi-trader behavior
- live/paper/backtest semantic alignment
- event schemas
- snapshot/checkpoint logic
- replay logic

## Handoff requirements
Every session must update `/status/session_handoff.md` with:
- task attempted
- scope boundary
- files changed
- what was intentionally left unchanged
- validations run
- result
- blockers
- new backlog items discovered
- next recommended task

## Failure handling
If blocked:
- stop broadening scope
- record the blocker clearly
- preserve partial findings in durable artifacts
- recommend the next smallest viable task
- do not solve blockers by broad architectural rewrites unless the blocker itself is the scoped task
