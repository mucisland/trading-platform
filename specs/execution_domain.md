# Execution Domain Specification

## Purpose

This document defines how trading decisions are converted into executable orders and how the system interacts with external trading venues.

The execution domain is responsible for:

- transforming trading intents into orders
- managing the order lifecycle
- interacting with venue adapters
- emitting order and fill events

---

## Core principle

The execution domain is **mechanical and non-decision-making**.

It must:

- execute instructions deterministically
- not introduce strategy or timing decisions
- not modify trading intent semantics

---

## Responsibilities

The execution domain must:

- receive trading intents from trader runtimes
- convert intents into orders
- send orders to venue adapters
- receive acknowledgements and fills
- emit canonical order and fill events to the ledger

---

## Inputs

The execution domain receives:

- trading intents from trader runtimes

A trading intent includes:

- instrument
- side (buy/sell)
- size
- optional execution parameters (e.g. limit price)

---

## Outputs

The execution domain must emit:

### Order events
- order created
- order acknowledged
- order rejected
- order canceled (if applicable)

---

### Fill events
- partial fill
- full fill

All events must be forwarded to the ledger domain.

---

## Order lifecycle

The execution domain must model the full lifecycle:

1. intent received
2. order created
3. order sent to venue
4. order acknowledged or rejected
5. order partially or fully filled
6. order completed or terminated

---

## Determinism

The execution domain must:

- behave deterministically given identical inputs
- produce identical order events during replay

It must not:

- depend on non-replayable inputs
- introduce randomness

---

## Venue adapters

Execution interacts with external systems via adapters.

Adapters must:

- translate between internal order format and venue API
- handle connectivity and protocol specifics
- emit canonical events back to execution domain

Adapters must not:

- implement trading logic
- modify order intent semantics

---

## Failure handling

The execution domain must handle:

- order rejection
- partial fills
- delayed acknowledgements
- temporary connectivity issues

In all cases:

- state must remain consistent
- events must be emitted
- ledger must remain authoritative

---

## Idempotency

Execution must tolerate:

- duplicate intent submission
- replay of order events

Repeated processing must not:

- create duplicate orders
- corrupt order state

---

## Interaction with ledger

Execution must:

- emit all order and fill events to the ledger
- not maintain authoritative state independently

The ledger is the source of truth.

---

## Interaction with trader runtime

Execution must:

- accept intents from trader runtimes
- not feed back decisions into strategy logic

Feedback is limited to:

- order status
- fills

---

## Degraded mode

In degraded mode:

- new order submission may be restricted
- execution must not create inconsistent state
- existing orders must be tracked and updated

Execution must remain consistent with ledger state.

---

## Invariants

The following must always hold:

- execution does not make strategy decisions
- all orders originate from trader intents
- all fills are recorded in the ledger
- order lifecycle is fully represented
- behavior is deterministic under replay
- duplicate processing is safe (idempotent)

---

## Observability

The system must expose:

- order lifecycle state
- outstanding orders
- fill activity
- execution errors

---

## Core guarantee

Given a sequence of trading intents and market responses:

The execution domain must produce a consistent, replayable sequence of order and fill events without altering trading intent semantics.
