# Interface Contracts Specification

## Purpose

This document defines the logical interfaces between the system domains.

It specifies:
- inputs
- outputs
- permitted queries
- forbidden dependencies
- behavioral guarantees

These contracts are normative and must be preserved by implementation.

---

## General contract rules

All domain interfaces must follow these rules:

- interfaces must be explicit
- inputs and outputs must be deterministic
- correctness-critical flows must be replayable
- interfaces must not leak internal implementation details
- consumers must depend on canonical data, not source-specific formats
- cross-domain communication must preserve ordering and traceability where required

A domain may only depend on another domain through its defined interface.

---

## 1. Market Domain Interface

### Purpose
Provide canonical market events to all downstream consumers.

### Inputs
- raw market data from exchanges or data providers
- historical market data for replay
- instrument metadata from external sources

### Outputs
- canonical quote events
- canonical trade events
- canonical instrument metadata events
- market data integrity/degraded-state signals

### Consumers
- Trader Runtime
- Replay / Recovery processes
- Runtime Control

### Permitted queries
- latest canonical market state for an instrument
- instrument metadata lookup
- replay stream from a defined point

### Forbidden dependencies
- must not depend on Trader Runtime
- must not depend on Risk
- must not depend on Execution
- must not depend on Ledger for correctness of live market normalization

### Guarantees
- events are canonical
- per-stream ordering is deterministic
- missing or invalid data is detected
- replay emits equivalent canonical events

---

## 2. Trader Runtime Interface

### Purpose
Consume canonical market/account context and produce trading intents.

### Inputs
- canonical market events
- own order events
- own fill events
- own position/account updates
- trader-local configuration
- replay stream during recovery

### Outputs
- strategy signals (internal)
- approved local trading intents
- trader-local degraded/readiness state
- trader state snapshots/checkpoints

### Consumers
- Risk / Portfolio (local, if separated internally)
- Runtime Control
- Recovery processes

### Permitted queries
- own current position/account state
- own configuration
- own recovery/snapshot state
- instrument metadata from canonical sources

### Forbidden dependencies
- must not access other traders’ state
- must not access venue adapters
- must not access Execution directly except through defined intent submission
- must not access raw market data

### Guarantees
- behavior is deterministic under replay
- output depends only on canonical inputs and trader-local state
- state can be reconstructed from snapshot + replay
- no hidden correctness-critical state exists outside recovery contract

---

## 3. Risk and Portfolio Interface

### Purpose
Evaluate trader-produced intents against local capital and position constraints.

### Inputs
- trading intents from Trader Runtime
- trader-local capital allocation
- own current positions from Ledger
- own fill/order state from Ledger
- degraded-state signals from Runtime Control

### Outputs
- approved intents
- rejected intents
- resized/reshaped intents
- rejection reasons
- trader-local risk state

### Consumers
- Execution Domain
- Trader Runtime
- Runtime Control
- Observability

### Permitted queries
- own position state
- own available capital
- own fill/order history relevant to local risk
- degraded-state status

### Forbidden dependencies
- must not access other traders’ state
- must not access venue adapters
- must not alter strategy timing logic
- must not maintain authoritative portfolio truth independently of Ledger

### Guarantees
- every executed trade has passed risk evaluation
- risk decisions are deterministic
- no trade exceeds trader allocation constraints
- degraded mode blocks new exposure as specified

---

## 4. Execution Domain Interface

### Purpose
Transform approved intents into orders and manage order lifecycle against venues.

### Inputs
- approved intents from Risk / Portfolio
- venue capability information
- runtime degraded/halt signals
- acknowledgements/fills/rejections from venue adapters

### Outputs
- canonical order events
- canonical fill events
- execution-status events
- execution errors
- order lifecycle state updates

### Consumers
- Ledger / Recovery
- Trader Runtime
- Runtime Control
- Observability

### Permitted queries
- venue capability lookup
- current order lifecycle state
- own pending order state
- runtime trading permission status

### Forbidden dependencies
- must not make strategy decisions
- must not modify trading intent semantics beyond mechanical realization
- must not own authoritative recoverable state independently of Ledger

### Guarantees
- all order lifecycle transitions are explicit
- all fills and order events are emitted canonically
- behavior is idempotent with respect to duplicate inputs/events
- replay preserves the same lifecycle semantics

---

## 5. Venue Adapter Interface

### Purpose
Translate between canonical internal execution requests and venue-specific APIs.

### Inputs
- canonical order requests from Execution
- connection/session control signals
- venue-specific configuration

### Outputs
- acknowledgements
- rejections
- fills
- connection/health events
- canonicalized venue response events back to Execution

### Consumers
- Execution Domain
- Runtime Control
- Observability

### Permitted queries
- venue capability and constraint information
- adapter-local connection state

### Forbidden dependencies
- must not contain strategy logic
- must not contain risk logic
- must not emit directly to Trader Runtime or Ledger except through Execution-defined flows

### Guarantees
- translation is deterministic
- venue-specific details are not leaked past the adapter boundary except through explicit capability contracts
- connection/health failures are observable

---

## 6. Ledger and Recovery Interface

### Purpose
Maintain the authoritative recoverable trading state and support deterministic recovery.

### Inputs
- canonical order events
- canonical fill events
- position update events
- checkpoint requests
- replay/recovery control requests

### Outputs
- authoritative position state
- authoritative order state
- authoritative fill history
- checkpoints
- recovery state and replay boundaries
- trader-visible own-account state streams

### Consumers
- Trader Runtime
- Risk / Portfolio
- Runtime Control
- Recovery processes
- Observability

### Permitted queries
- current positions
- current order state
- fill history
- checkpoint metadata
- replay starting points

### Forbidden dependencies
- must not make trading decisions
- must not depend on in-memory trader state for correctness
- must not allow other domains to redefine authoritative state outside event ingestion

### Guarantees
- ledger state is sufficient for recovery
- operations are idempotent
- event ordering is preserved
- replay from a valid checkpoint reconstructs correct state

---

## 7. Runtime Control Interface

### Purpose
Manage lifecycle, degraded mode, readiness, halt/resume, and recovery orchestration.

### Inputs
- degraded-state signals from Market, Trader, Execution, Ledger
- recovery status
- validation of readiness invariants
- operator or harness control signals

### Outputs
- runtime mode transitions
- degraded/halt signals
- resume permissions
- readiness state
- recovery orchestration state

### Consumers
- Trader Runtime
- Risk / Portfolio
- Execution
- Observability
- Harness / recovery processes

### Permitted queries
- current runtime mode
- current degraded/halt state
- readiness state for platform and traders
- recovery progress

### Forbidden dependencies
- must not implement strategy logic
- must not directly mutate ledger truth
- must not bypass domain invariants when restoring service

### Guarantees
- runtime mode is explicit
- degraded and recovery states are observable
- resume only occurs when defined invariants are satisfied

---

## 8. Cross-domain flow contracts

### Market -> Trader
- Trader receives only canonical market events
- Trader must not depend on raw source details

### Trader -> Risk
- Trader emits trading intents, not executable orders
- intent semantics must be explicit and traceable

### Risk -> Execution
- only approved intents may cross this boundary
- rejection reasons must remain observable upstream

### Execution -> Ledger
- all order/fill lifecycle events must be emitted canonically
- Ledger becomes authoritative from this boundary onward

### Ledger -> Trader/Risk
- only own-account / own-position / own-order state is visible to a trader
- cross-trader visibility is forbidden

### Runtime Control -> All domains
- degraded/halt/readiness signals are authoritative for lifecycle control
- domains must not silently ignore them

---

## 9. Interface stability rules

- interface changes must be explicit and documented
- changes to event semantics require spec updates
- consumers must not infer undocumented fields or behaviors
- implementation convenience must not override interface boundaries

---

## 10. Minimal implementation guidance

The first implementation should preserve these logical contracts even if:
- multiple domains initially live in one process
- transport is in-memory
- persistence is simplified

Physical deployment may change later.
Logical boundaries must remain stable.
