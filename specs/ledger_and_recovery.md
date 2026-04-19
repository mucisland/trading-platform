# Ledger and Recovery Specification

## Purpose

This document defines the authoritative state model of the system and the mechanisms required to support restart and deterministic recovery.

It is the foundation for:

- restartability
- replay correctness
- state consistency
- crash tolerance

---

## Core principle

The ledger is the **single source of truth** for all recoverable system state.

All correctness-critical decisions must be reproducible from:

- market events
- ledger state

No other state may be required for correctness.

---

## Responsibilities

The ledger domain must:

- persist all orders, fills, and positions
- maintain a consistent and ordered event history
- provide a complete reconstruction of trading state
- support replay from any valid point in time
- enable recovery after crashes without loss of correctness

---

## Stored entities

The ledger must store:

### Orders
- order id
- instrument
- side
- size
- price (if applicable)
- timestamps
- status (created, acknowledged, rejected, etc.)

---

### Fills
- fill id
- order id
- executed size
- execution price
- timestamp

---

### Positions
- instrument
- net position
- average entry price
- realized PnL
- position lifecycle state

---

## Event model

Ledger state must be derived from an **ordered event stream**.

Event properties:

- immutable
- timestamped
- strictly ordered within a stream
- replayable

---

## Ordering guarantees

The system must ensure:

- deterministic ordering of ledger-relevant events
- no ambiguity in event sequencing during replay
- consistent ordering between live and replay modes

---

## Idempotency

All ledger operations must be idempotent.

The system must tolerate:

- duplicate event delivery
- replay of already-processed events

Processing the same event multiple times must not change the final state.

---

## Consistency guarantees

The ledger must guarantee:

- internal consistency of positions
- consistency between orders and fills
- no loss or duplication of executed trades

---

## Recovery model

Recovery consists of reconstructing system state after a restart.

Recovery must:

1. restore ledger state
2. replay market and execution events
3. reconstruct trader state
4. resume live operation when invariants are satisfied

---

## Recovery inputs

Recovery uses:

- persisted ledger state
- historical market events
- historical order and fill events

No in-memory state may be required.

---

## Replay process

Replay must:

- feed events to traders in original order
- allow strategies to rebuild internal state
- produce identical decisions as live execution

Replay must not:

- skip events
- reorder events
- inject synthetic behavior unless explicitly defined

---

## Replay boundary

The system must define a clear replay boundary:

- from last known consistent checkpoint
- or from the beginning of the relevant event history

---

## Checkpointing

The system may use checkpoints to:

- reduce replay time
- provide known-good recovery points

A checkpoint must include:

- complete ledger state
- sufficient information to resume replay deterministically

Checkpoints must be:

- consistent
- durable
- explicitly identifiable

---

## Crash behavior

On crash:

- in-memory state is considered lost
- no assumptions may be made about partial processing
- recovery must rely only on durable data

---

## Incomplete state detection

The system must detect:

- missing events
- gaps in event streams
- inconsistent ledger state

If detected:

- system must enter degraded mode
- recovery must not proceed to live operation until resolved

---

## Degraded recovery

During recovery:

- system operates in degraded mode
- no new positions may be opened
- existing positions may be managed conservatively

Transition to normal operation requires:

- complete and consistent state
- replay completion
- invariant satisfaction

---

## Interaction with other domains

### Trader Runtime
- reconstructs internal state from replay
- must not rely on ledger internals beyond defined interfaces

---

### Execution Domain
- emits order and fill events
- must not assume ledger state beyond confirmations

---

### Market Domain
- provides replayable market data
- must ensure event completeness

---

## Invariants

The following must always hold:

- ledger state is sufficient for full recovery
- no correctness depends on in-memory-only data
- replay produces identical state as live processing
- event ordering is deterministic
- ledger operations are idempotent
- incomplete state is detected and handled

---

## Observability

The system must expose:

- current ledger state
- replay progress
- recovery status
- detected inconsistencies

---

## Failure handling

If ledger invariants are violated:

- system must not proceed to live trading
- system must enter degraded mode
- recovery or rollback must be initiated

---

## Core guarantee

At any point in time:

The system must be able to:

- stop execution
- restart from durable state
- replay events
- arrive at the same trading state and decisions
