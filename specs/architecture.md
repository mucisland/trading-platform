# Architecture Specification

## Purpose

This document defines the high-level structure of the trading platform and the separation of concerns between its domains.

It is the authoritative source for:
- component boundaries
- responsibility assignment
- system-wide invariants

## Architectural principles

The system must optimize for:

1. restartability
2. simplicity
3. observability
4. safety / loss prevention
5. extensibility

## System decomposition

The platform is composed of the following domains:

- Market Domain
- Trader Runtime (multiple instances)
- Execution Domain
- Ledger / Recovery Domain
- Runtime Control Domain

## Core structure

The system models:

- a single market environment
- multiple independent trader instances

Each trader instance:
- runs one strategy
- has local risk and allocation logic
- operates independently of other traders

## Domain boundaries

### Market Domain
- produces canonical market events
- is shared by all traders
- does not depend on traders

### Trader Runtime
- consumes market events
- produces trading intents
- contains:
  - strategy
  - local risk
  - allocation

### Execution Domain
- converts trading intents into executable orders
- interacts with venue adapters
- must not contain strategy logic

### Ledger / Recovery Domain
- stores authoritative state:
  - orders
  - fills
  - positions
- supports restart and replay
- is the source of truth for recovery

### Runtime Control Domain
- manages readiness
- manages degraded states
- controls automatic resume

## Invariants

The system must enforce:

- strategy code must not interact with venue adapters directly
- execution must not make strategy decisions
- ledger is the authoritative state for recovery
- correctness must not depend on graceful shutdown
- all correctness-critical streams must be durably captured

## Multi-trader model

- each trader is fully isolated in logic and state
- traders do not see each other's positions or decisions
- traders share only:
  - market data
  - execution infrastructure

## Failure model

- crashes are expected and normal
- system must recover without loss of correctness
- degraded states must be explicit and controlled
