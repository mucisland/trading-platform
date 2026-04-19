# System Overview

## Purpose

The system is an autonomous trading platform designed to:

- run multiple trading strategies concurrently
- evaluate and evolve strategies through research and backtesting
- execute trades in live markets within defined risk constraints
- operate continuously and unattended over long time horizons

---

## Mode of operation

The platform models:

- a single shared market environment
- multiple independent trader instances

Each trader:
- runs exactly one strategy configuration
- consumes canonical market events
- produces trading decisions
- manages its own risk and capital allocation

Traders are isolated from each other in logic and state.

---

## Core principles

The system must optimize for:

1. restartability
2. correctness under replay
3. simplicity of reasoning
4. observability of all states
5. safety with respect to capital

---

## Restartability-first design

Restartability is a primary system property, not an afterthought.

The system must:

- tolerate process termination at any time
- recover without loss of decision correctness
- reconstruct all required state from durable data
- treat crashes as normal operational events

Correctness must not depend on:
- graceful shutdown
- in-memory-only state
- implicit sequencing assumptions

---

## Replay correctness

The system must support deterministic replay.

Replay must:

- reconstruct trader state from historical events
- produce the same decisions as live execution
- allow strategies to rebuild indicators and internal state

The system must not:

- rely on non-deterministic inputs
- behave differently in replay vs live unless explicitly controlled

Live semantics are primary; replay must approximate them closely.

---

## Degraded mode semantics

The system must explicitly represent degraded states.

Degraded mode is entered when:
- event streams are incomplete
- replay is in progress
- system invariants are not satisfied

In degraded mode:

- no new positions may be opened
- existing positions may be managed
- risk remains active
- system must work toward restoring a non-degraded state

Degraded operation must be:
- explicit
- observable
- bounded in behavior

---

## High-level flow

1. Market data is ingested and normalized into canonical events
2. Traders consume events and update internal state
3. Strategies produce trading signals
4. Risk evaluates and shapes trading decisions
5. Execution domain converts decisions into orders
6. Orders and fills are recorded in the ledger
7. Ledger enables replay and recovery at any time

---

## State model

- Market data is external and replayable
- Trader state is derived and reconstructible
- Ledger is the authoritative source of truth

All correctness-critical data must be:
- durable
- ordered
- replayable

---

## Failure model

Failures are expected and must be treated as normal:

- process crashes
- partial data availability
- temporary inconsistencies

The system must:

- detect invalid or incomplete state
- enter degraded mode when required
- recover automatically when invariants are satisfied

---

## Success criteria

The system is correct when:

- trading decisions are consistent between live and replay
- restart does not degrade strategy correctness
- degraded states are handled safely and explicitly
- traders remain isolated and independent
- risk constraints are always enforced
- the platform can run unattended for extended periods

---

## Non-goals

The following are explicitly out of scope for the current system:

- global portfolio optimization across traders
- cross-strategy coordination or shared decision-making
- high-frequency or ultra-low-latency trading optimization
- reliance on manual intervention for recovery
- implicit or hidden system state outside durable storage
- complex dynamic resource scheduling across traders

These may be introduced in later system evolutions but must not influence current architecture or implementation decisions.
