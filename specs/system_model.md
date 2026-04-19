# System Model Specification

## Purpose

This document defines the fundamental data and event model of the system.

---

## Event-driven model

The system operates on event streams:

- market events
- order events
- fill events
- position updates

All domains communicate via events.

---

## Canonical event types

### Market events
- quotes
- trades
- instrument metadata

---

### Order events
- order created
- order acknowledged
- order rejected

---

### Fill events
- partial fill
- full fill

---

### Position events
- position opened
- position updated
- position closed

---

## Event properties

All events must be:

- timestamped
- ordered (within a stream)
- replayable
- deterministic

---

## Replay model

The system must support:

- replay from historical data
- replay after crash
- replay to reconstruct trader state

Replay must produce the same results as live processing.

---

## Live vs replay

- live semantics are primary
- replay must approximate live behavior
- no logic may depend on "being in replay mode"

---

## Data ownership

- Market Domain owns market events
- Trader Runtime owns internal signals
- Ledger owns orders, fills, positions

---

## Consistency

- event streams must be complete
- missing data must be detected
- degraded mode must be entered if required
