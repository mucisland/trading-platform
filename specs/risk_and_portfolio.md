# Risk and Portfolio Specification

## Purpose

This document defines how trading decisions are validated, constrained, and shaped before execution.

It ensures:

- capital safety
- adherence to trading constraints
- controlled behavior in degraded conditions

---

## Core principle

Risk is **authoritative over trade approval and sizing**, but must not interfere with strategy timing decisions.

---

## Responsibilities

The risk and portfolio domain must:

- evaluate trading intents
- approve or reject trades
- adjust trade size based on available capital
- enforce per-trader allocation constraints
- manage existing positions safely

---

## Scope

Risk operates:

- per trader instance
- within that trader's allocated capital

There is no global portfolio optimization in v1.

---

## Inputs

Risk receives:

- trading intents from strategy
- current position state (from ledger)
- available capital for the trader

---

## Outputs

Risk produces:

- approved trading intents
- modified trading intents (e.g. reduced size)
- rejected trading intents

Rejected trades must not reach execution.

---

## Trade approval logic

Risk may:

- approve trades
- reject trades
- reduce trade size

Risk must not:

- delay trades
- reorder trades
- modify strategy timing decisions

---

## Capital allocation

Each trader operates within:

- a fixed capital allocation

Risk must ensure:

- trades do not exceed available capital
- position limits are respected

---

## Position management

Risk must:

- track current positions (via ledger)
- ensure position constraints are respected
- allow safe management of existing positions

---

## Degraded mode behavior

In degraded mode:

- no new positions may be opened
- existing positions may be managed (e.g. reduced or closed)
- risk must enforce conservative behavior

---

## Restart and replay

Risk behavior must be:

- deterministic under replay
- consistent with live execution

Risk must rely only on:

- ledger state
- replayed events

---

## Interaction with trader runtime

Risk sits between:

- strategy (signal producer)
- execution (order executor)

Flow:

strategy → risk → execution

---

## Interaction with ledger

Risk must:

- use ledger as the source of truth for:
  - positions
  - fills
- not maintain independent authoritative state

---

## Invariants

The following must always hold:

- no trade exceeds available capital
- rejected trades are not executed
- position limits are enforced
- risk decisions are deterministic
- degraded mode restricts new exposure
- risk does not alter trade timing

---

## Failure handling

If inconsistencies are detected:

- system must enter degraded mode
- new trades must be restricted
- recovery must be initiated if necessary

---

## Observability

The system must expose:

- current allocation per trader
- position sizes
- rejected trades
- reasons for rejection
- risk-adjusted trade sizes

---

## Core guarantee

All trades executed by the system:

- are within defined capital constraints
- have passed deterministic risk evaluation
- remain consistent under replay and recovery
