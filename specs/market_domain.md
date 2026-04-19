# Market Domain Specification

## Purpose

This document defines how market data is ingested, normalized, and distributed within the system.

The market domain is responsible for:

- acquiring market data from external sources
- normalizing data into canonical events
- ensuring completeness and ordering
- providing a replayable event stream to all consumers

---

## Core principle

Market data is the **external ground truth** of the system.

All trading decisions must be based solely on:

- canonical market events
- deterministic internal state derived from those events

---

## Responsibilities

The market domain must:

- ingest market data from one or more sources
- normalize data into canonical event formats
- assign timestamps and ordering
- detect missing or inconsistent data
- provide a continuous event stream
- support deterministic replay

---

## Inputs

The market domain receives raw data from:

- exchanges
- data providers
- historical datasets (for replay)

Raw data may include:

- quotes (bid/ask)
- trades
- instrument metadata

---

## Canonical market events

All input data must be transformed into canonical events.

### Quote events
- instrument
- bid price
- bid size
- ask price
- ask size
- timestamp

---

### Trade events
- instrument
- price
- size
- timestamp

---

### Instrument metadata
- symbol
- instrument type (equity, option, FX)
- relevant parameters (e.g. expiry, strike)

---

## Event properties

All canonical market events must be:

- timestamped
- immutable
- ordered within a stream
- uniquely identifiable (if required)
- replayable

---

## Ordering guarantees

The system must ensure:

- deterministic ordering of events within each instrument stream
- consistent ordering between live and replay modes

If strict global ordering is not feasible:

- per-instrument ordering must be guaranteed
- cross-instrument ordering must be explicitly defined or treated as independent

---

## Completeness

The market domain must detect:

- gaps in data
- missing events
- out-of-order delivery

If detected:

- system must enter degraded mode
- affected traders must not operate on incomplete data

---

## Replay support

The market domain must support:

- replay from historical datasets
- replay after system restart

Replay must:

- produce identical event sequences as originally observed
- preserve ordering and timing semantics (to the extent required)

---

## Live vs replay behavior

The system must not rely on:

- implicit differences between live and replay data

Replay must:

- approximate live behavior closely
- not introduce artificial artifacts unless explicitly defined

---

## Event distribution

The market domain must:

- provide the same event stream to all trader instances
- ensure consistent ordering across consumers

Traders must not:

- receive diverging market data views

---

## Latency considerations

Latency is not a primary optimization goal in v1.

The system must prefer:

- correctness
- determinism
- completeness

over minimal latency.

---

## Interaction with trader runtime

Traders:

- consume canonical market events
- must not access raw market data
- must not depend on source-specific details

---

## Interaction with replay and recovery

Market events must:

- be stored or accessible for replay
- be sufficient to reconstruct trader state

Replay must:

- feed events into traders in the same order as live processing

---

## Degraded mode

The system must enter degraded mode if:

- market data is incomplete
- event ordering cannot be guaranteed
- data source becomes unreliable

In degraded mode:

- traders must not open new positions
- system must attempt to restore data integrity

---

## Invariants

The following must always hold:

- all trading decisions are based on canonical market events
- event ordering is deterministic
- missing data is detected and handled
- replay produces identical event sequences
- traders receive consistent market data
- no logic depends on raw data source specifics

---

## Observability

The system must expose:

- current market data state
- data source status
- detected gaps or inconsistencies
- replay progress (if applicable)

---

## Failure handling

If market data invariants are violated:

- system must enter degraded mode
- trading must be restricted
- recovery procedures must be initiated

---

## Core guarantee

At any point in time:

The system must be able to:

- reconstruct the exact sequence of market events
- replay them deterministically
- produce identical trading decisions from those events
