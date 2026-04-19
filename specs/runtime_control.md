# Runtime Control Specification

## Purpose

This document defines the lifecycle control of the platform.

The runtime control domain is responsible for:

- managing platform and trader runtime states
- detecting and representing degraded conditions
- controlling halt and resume behavior
- coordinating recovery and replay
- deciding when live operation may continue

---

## Core principle

Runtime control is the authoritative source for lifecycle state.

All domains must treat runtime state as explicit and binding.

No domain may silently continue normal behavior when runtime control indicates:
- degraded mode
- halted mode
- recovery in progress
- not ready

---

## Responsibilities

The runtime control domain must:

- maintain platform-level runtime state
- maintain trader-level readiness and degraded state
- consume health and integrity signals from other domains
- enforce transitions between runtime states
- coordinate automatic resume when invariants are satisfied
- expose lifecycle state for observability and control

---

## Runtime state model

The platform must represent at least the following runtime states:

- initializing
- recovering
- degraded
- ready
- halted

These states are explicit and mutually meaningful.

---

## State meanings

### Initializing
The platform is starting and basic services are not yet ready.

In this state:
- no live trading is allowed
- readiness is false
- replay may not yet begin

---

### Recovering
The platform is reconstructing state after startup or failure.

In this state:
- ledger state is being restored
- replay may be in progress
- no new positions may be opened
- readiness is false

---

### Degraded
The platform is running, but one or more invariants required for normal operation are not satisfied.

In this state:
- new positions may not be opened
- existing positions may be managed conservatively
- readiness is false for normal trading
- observability must clearly indicate the degraded reason

---

### Ready
The platform is healthy and all required invariants are satisfied.

In this state:
- normal live trading is allowed
- replay is complete
- readiness is true

---

### Halted
The platform is explicitly prevented from trading.

In this state:
- no new trades are allowed
- execution of new exposure is forbidden
- only explicitly allowed shutdown or protective management actions may occur

---

## Scope of state

Runtime state exists at two levels:

### Platform-level state
Represents the overall system lifecycle.

### Trader-level state
Represents readiness and degraded status for each trader instance.

The platform must track both.

---

## State authority

Runtime control owns:

- platform state
- trader readiness state
- trader degraded state
- resume permission
- halt status

Other domains may emit signals, but must not authoritatively redefine runtime state.

---

## Inputs

Runtime control receives signals from:

- Market Domain
- Trader Runtime
- Risk and Portfolio
- Execution Domain
- Ledger and Recovery
- Harness or operator controls

These signals may include:
- data integrity failures
- recovery completion
- replay completion
- invariant violations
- explicit halt requests

---

## Outputs

Runtime control emits:

- platform runtime state
- trader runtime state
- degraded reasons
- halt/resume permissions
- readiness signals
- recovery orchestration signals

---

## Degraded state triggers

Runtime control must enter degraded mode when any required invariant for normal operation is violated.

Examples include:
- incomplete market data
- unresolved ledger inconsistency
- replay not complete
- trader state not reconstructed
- execution or adapter state not trustworthy

The exact invariant set must be observable.

---

## Halt triggers

Runtime control must enter halted state when:
- an explicit halt is requested
- a safety-critical invariant requires full stop
- automatic continuation would be unsafe

---

## Resume conditions

Transition to ready is allowed only when all required invariants are satisfied.

These include at minimum:

- market data integrity is acceptable
- ledger state is consistent
- replay is complete
- trader state reconstruction is complete
- required runtime dependencies are healthy
- no active halt condition exists

---

## Automatic resume

Automatic resume is allowed when:
- runtime control determines all defined invariants are satisfied
- no explicit halt is active
- recovery has completed successfully

Automatic resume must be deterministic and observable.

---

## Forbidden behavior

Runtime control must not:
- implement strategy logic
- modify trading decisions
- silently relax invariants
- bypass degraded or halt constraints
- rely on hidden in-memory assumptions not captured in recovery state

---

## Trader-level behavior

Each trader must expose at least:

- readiness state
- degraded state
- degraded reason (if applicable)
- recovery progress (if applicable)

Runtime control must aggregate these into platform-level readiness.

A platform may be non-ready because:
- one or more required traders are not ready
- shared platform invariants are not satisfied

---

## Interaction with recovery

Recovery is orchestrated through runtime control.

Runtime control must:

1. enter recovering state when restoration begins
2. remain non-ready while replay is incomplete
3. transition to degraded or ready depending on invariant evaluation
4. prevent normal live trading during incomplete recovery

---

## Interaction with execution

Execution must obey runtime control signals.

If runtime control indicates:
- degraded
- halted
- not ready

then execution must not create new exposure unless explicitly allowed by policy.

---

## Interaction with risk

Risk must obey runtime control signals.

If runtime control indicates degraded or halted conditions:
- risk must reject or constrain new exposure appropriately

---

## Invariants

The following must always hold:

- runtime state is explicit
- no normal live trading occurs unless runtime state is ready
- degraded conditions are detectable and observable
- resume occurs only after invariant satisfaction
- halt state is authoritative
- trader and platform readiness are distinct but coherent

---

## Observability

The system must expose:

- current platform runtime state
- current trader runtime state per trader
- degraded reasons
- halt reasons
- replay/recovery progress
- readiness status

---

## Failure handling

If runtime control cannot determine a trustworthy ready state:
- system must remain degraded or halted
- normal live trading must not resume
- recovery or planning intervention must be required

---

## Core guarantee

The platform must never trade in normal mode unless runtime control has explicitly determined that the system is ready and its required invariants are satisfied.
