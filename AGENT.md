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

## Core workflow rules
- perform exactly one scoped task per session
- search the codebase before assuming missing implementation
- do not broaden scope implicitly
- if unrelated issues are discovered, record them in backlog instead of fixing them unless they block the current task
- update handoff and backlog artifacts at the end of every session
- prefer modifying existing abstractions over creating parallel ones

## Environment setup rules
At the start of every session run:

```
./scripts/session_init.sh
./scripts/verify_env.sh
```

If the current task needs local infrastructure, also run:

```
./scripts/start_local_services.sh
```

Do not invent ad hoc setup when scripted setup exists. Do not silently work around environment failures. Record blocking setup failures in `/status/session_handoff.md` and `/backlog/fix_plan.md`.

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

Run the smallest sufficient validation set for the current task. Default fast lane:

```
./scripts/run_fast_checks.sh
```

Escalate only when the task touches:
- recovery
- cross-domain boundaries
- execution behavior
- multi-trader behavior
- live/paper/backtest semantic alignment

## Handoff requirements
Every session must update `/status/session_handoff.md` with:
- task attempted
- scope boundary
- files changed
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
