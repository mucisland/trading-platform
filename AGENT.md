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

---

## Architectural priorities
Always optimize in this order unless an explicit architecture decision says otherwise:
1. restartability
2. simplicity
3. observability
4. safety / loss prevention
5. extensibility

When priorities conflict, prefer the higher-ranked priority unless explicitly overridden in repository artifacts.

---

## Operating modes

### Implementation mode
Used when executing a defined backlog task.

Constraints:
- exactly one backlog item
- no scope expansion
- minimal context loading
- targeted validation only

### Planning mode
Used when:
- no valid task exists
- backlog is ambiguous or incomplete
- blocked by missing decisions

Output:
- updated `/backlog/fix_plan.md`
- clarified tasks
- new discovered work

Do not mix planning and implementation in the same session.

---

## Core workflow loop

Every session follows:

1. **Initialize environment**
    ./scripts/session_init.sh
    ./scripts/verify_env.sh

2. **Select task**
- select exactly one task from `/backlog/fix_plan.md`
- prefer highest-priority non-blocked task

3. **Load minimal context**
- AGENT.md
- one backlog item
- 1–3 relevant spec files
- one runbook
- touched files only

4. **Search before acting**
- do not assume missing implementation
- inspect codebase first

5. **Execute scoped change**
- modify only required components
- do not expand scope

6. **Validate**
    ./scripts/run_fast_checks.sh

7. **Write artifacts**
- update `/status/session_handoff.md`
- update `/backlog/fix_plan.md`

---

## Task selection rules

- all implementation work must originate from `/backlog/fix_plan.md`
- do not invent new tasks outside backlog
- if no suitable task exists → switch to planning mode
- do not modify multiple backlog items in one session
- if task is unclear → refine it before implementation

---

## Artifact-driven memory model

Persistent state lives in:
- `/backlog/fix_plan.md` → planning
- `/status/session_handoff.md` → execution continuity
- `/specs/*.md` → correctness definitions
- `/runbooks/*.md` → procedures

Do not rely on implicit memory or prior sessions.

---

## Boundary preservation rules

### Strategy layer
- must not talk to venue adapters
- must not emit executable orders

### Trader isolation
- must not access other traders’ internal state
- may only consume allowed event/account context

### Risk layers
- local risk must not bypass global risk

### Execution
- must not make strategy decisions

### Ledger / recovery
- authoritative for recoverable truth

### Runtime control
- governs readiness and resume

### General
- do not introduce implicit netting or cross-trader coordination
- do not introduce correctness dependencies on in-memory-only state
- recovery must use snapshot + replay contract
- replay must complete before live rejoin

---

## Restartability rules

- correctness must not depend on graceful shutdown
- crash is a normal condition
- all correctness-critical streams must be durable
- replay must reconstruct correct decision state
- no hidden state outside recovery contract

---

## Environment rules

At session start:

    ./scripts/session_init.sh
    ./scripts/verify_env.sh

If needed:

    ./scripts/start_local_services.sh

If setup fails:
- stop implementation
- record failure
- switch to environment-fix task

---

## Validation rules

Default:

    ./scripts/run_fast_checks.sh

Escalate when touching:
- recovery
- execution
- multi-trader behavior
- cross-domain boundaries
- event schemas
- replay/snapshots

---

## Handoff requirements

Every session must update `/status/session_handoff.md`:

- task attempted
- scope boundary
- files changed
- what was intentionally unchanged
- validation results
- blockers
- new backlog items
- next task

---

## Failure handling

If blocked:
- stop expanding scope
- record blocker clearly
- do not workaround silently
- do not perform large refactors
- recommend next smallest task

---

## Continuous improvement rule

If a failure pattern repeats:
- update runbooks or AGENT.md
- encode prevention as a rule
- do not rely on memory of failure

---

## Anti-drift rules

- do not optimize outside task scope
- do not refactor unrelated code
- do not add abstractions without need
- do not assume intent beyond artifacts

---

## Core principle

The agent is not trusted to:
- remember context
- infer missing design
- expand scope safely

The system is designed so that:
- artifacts define reality
- the harness enforces discipline
- each session is small, verifiable, and restartable
