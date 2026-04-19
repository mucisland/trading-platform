# Data Model Specification

## Purpose

This document defines the canonical shared entities used across the system.

It exists to ensure that all domains use consistent identifiers, fields, and semantics for correctness-critical data.

---

## Core principle

All domains must communicate using canonical shared models.

No domain may invent incompatible representations for:
- instruments
- market events
- trading intents
- orders
- fills
- positions
- trader identity
- runtime state

---

## General model rules

All correctness-critical entities must:

- have explicit identity where applicable
- use canonical field names and meanings
- be serializable
- be replayable where relevant
- be stable across live and replay modes

All timestamps must be explicit.

All identifiers must be stable within the system boundary.

---

## Identifier conventions

The system must define and preserve the following identifiers:

- `trader_id`
- `instrument_id`
- `order_id`
- `fill_id`
- `event_id` (where needed)
- `checkpoint_id` (where applicable)

Identifiers must be:

- unique within their required scope
- durable where relevant
- not derived from transient in-memory state only

---

## Timestamp conventions

All event-like entities must include a timestamp.

At minimum, timestamps must support:

- ordering within a stream
- replay reconstruction
- observability

Timestamp semantics must be documented consistently across domains.

---

## 1. Instrument model

### Purpose
Represent tradable entities in canonical form.

### Required fields
At minimum, an instrument must include:

- `instrument_id`
- `symbol`
- `asset_class`

### Asset classes
The system must support at least:
- equity
- option
- fx

### Additional fields by asset class

#### Equity
May include:
- exchange
- currency

#### Option
Must additionally support:
- underlying symbol or instrument
- expiry
- strike
- option type (call / put)

#### FX
Must additionally support:
- base currency
- quote currency

### Guarantees
- instruments are represented canonically across all domains
- domains do not depend on source-specific instrument encodings

---

## 2. Market event model

### Purpose
Represent canonical market data.

### Required common fields
All market events must include:

- `event_type`
- `instrument_id`
- `timestamp`

### Quote event
Must support:
- `bid_price`
- `bid_size`
- `ask_price`
- `ask_size`

### Trade event
Must support:
- `price`
- `size`

### Metadata event
Must support:
- `instrument_id`
- metadata payload sufficient for canonical instrument updates

### Guarantees
- market events are immutable
- fields have stable semantics
- replay uses the same model as live

---

## 3. Trading intent model

### Purpose
Represent trader output before execution.

### Required fields
A trading intent must include at least:

- `trader_id`
- `instrument_id`
- `side`
- `size`
- `intent_type`
- `timestamp`

### Optional fields
May include:
- limit price
- rationale or tags
- validity window
- basket identifier (for future multi-leg support)

### Semantics
A trading intent is:

- not an executable order
- a request for risk evaluation and mechanical realization
- attributable to exactly one trader

### Guarantees
- intent semantics are explicit
- execution must not reinterpret intent as strategy logic

---

## 4. Order model

### Purpose
Represent orders sent for execution.

### Required fields
An order must include at least:

- `order_id`
- `trader_id`
- `instrument_id`
- `side`
- `size`
- `timestamp`
- `status`

### Optional fields
May include:
- limit price
- venue identifier
- time-in-force
- parent intent identifier

### Status model
Order status must be explicit and include at least:
- created
- acknowledged
- rejected
- partially_filled
- filled
- canceled
- terminated

### Guarantees
- order lifecycle is explicit
- status transitions are observable
- replay preserves the same lifecycle semantics

---

## 5. Fill model

### Purpose
Represent completed execution events.

### Required fields
A fill must include at least:

- `fill_id`
- `order_id`
- `trader_id`
- `instrument_id`
- `size`
- `price`
- `timestamp`

### Guarantees
- fills are immutable
- fills are attributable to a single order and trader
- duplicate fill processing is safe through idempotent handling

---

## 6. Position model

### Purpose
Represent trader-visible position state.

### Required fields
A position must include at least:

- `trader_id`
- `instrument_id`
- `net_size`
- `average_entry_price`
- `realized_pnl`

### Optional fields
May include:
- unrealized_pnl
- lifecycle state
- open timestamp
- last update timestamp

### Guarantees
- positions are derived from ledger-authoritative events
- positions are not authoritative outside the ledger domain

---

## 7. Allocation model

### Purpose
Represent trader-local capital allocation.

### Required fields
An allocation must include at least:

- `trader_id`
- allocated capital amount
- available capital amount
- timestamp or version marker

### Guarantees
- allocation is explicit
- risk decisions reference canonical allocation values

---

## 8. Runtime state model

### Purpose
Represent lifecycle and readiness state in canonical form.

### Required fields
A runtime state entity must include at least:

- scope (`platform` or `trader`)
- subject identifier (platform or trader_id)
- state
- timestamp

### Supported states
At minimum:
- initializing
- recovering
- degraded
- ready
- halted

### Optional fields
May include:
- degraded reason
- halt reason
- readiness details

### Guarantees
- runtime state semantics are consistent across domains
- degraded and halt reasons are observable

---

## 9. Checkpoint model

### Purpose
Represent durable recovery checkpoints.

### Required fields
A checkpoint must include at least:

- `checkpoint_id`
- timestamp
- scope
- reference to ledger state
- replay boundary information

### Guarantees
- checkpoints are durable
- checkpoints are sufficient to support deterministic recovery when combined with replay data

---

## 10. Error and rejection model

### Purpose
Represent canonical failures or refusals.

### Required fields
A rejection or error event must include at least:

- timestamp
- source domain
- affected entity identifier (if applicable)
- reason code
- human-readable reason

### Guarantees
- rejection causes are observable
- blocked or rejected actions remain traceable across replay and debugging

---

## Field semantics

### Size
`size` must be interpreted consistently for a given instrument class and transaction type.

### Side
`side` must use canonical semantics:
- buy
- sell

### Prices
Prices must use canonical units and precision conventions per instrument class.

### PnL
PnL fields must distinguish at least:
- realized
- unrealized (if represented)

---

## Serialization and persistence

Canonical models must be representable in a durable serialized form suitable for:

- ledger persistence
- replay
- observability
- debugging

The exact physical serialization format is an implementation detail, but semantic fields are not.

---

## Invariants

The following must always hold:

- identifiers are stable and meaningful within scope
- market, intent, order, fill, and position semantics are canonical
- domains do not invent incompatible private variants of shared models
- live and replay use the same logical data model
- correctness-critical entities are serializable and durable where required

---

## Core guarantee

Every correctness-critical interaction in the system must be expressible using canonical shared models whose semantics remain stable across domains, sessions, replay, and recovery.
