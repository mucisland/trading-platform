# Project Rules

## Purpose

This file defines the project-specific constraints, invariants, and design priorities.

It specifies:
- architectural boundaries
- allowed and forbidden behaviors
- system invariants (e.g. restartability, isolation)
- project-specific tradeoff rules

These rules must not be violated during implementation.

They take precedence over general workflow rules when conflicts arise.

## Core architecture

The system consists of:
- shared platform core
- multiple trader instances

## Strategy layer

- must not talk to venue adapters
- must not emit executable orders

## Trader isolation

- must not access other traders’ internal state
- may only consume allowed event/account context

## Risk layers

- trader-local risk must not bypass global risk

## Execution

- must not make strategy decisions

## Ledger / recovery

- authoritative for recoverable truth

## Runtime control

- governs readiness and resume

## Restartability rules

- correctness must not depend on graceful shutdown
- crash is normal behavior
- all correctness-critical streams must be durable
- replay must reconstruct correct state
- no hidden state outside recovery contract

## Replay rules

- snapshot + replay required
- replay must complete before live rejoin

## Forbidden behavior

- implicit netting across traders
- hidden cross-trader coordination
- reliance on in-memory-only state for correctness

## Validation escalation (project-specific)

Escalate validation when changes affect:

- recovery behavior
- execution logic
- multi-trader interactions
- cross-domain boundaries
- event schemas
- snapshot or replay logic

These areas are correctness-critical for this system.

## Project priorities

For this project, optimize in this order unless an explicit recorded decision says otherwise:
1. restartability
2. simplicity
3. observability
4. safety / loss prevention
5. extensibility

When priorities conflict, prefer the higher-ranked priority unless explicitly overridden in repository artifacts.
