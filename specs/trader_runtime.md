# Trader Runtime Specification

## Purpose

This document defines the structure and behavior of a trader instance.

---

## Definition

A trader is an isolated runtime instance that:

- consumes market events
- applies a strategy
- evaluates risk
- produces trading intents

---

## Composition

Each trader contains:

- strategy module
- local risk module
- allocation logic

---

## Responsibilities

A trader must:

- process market events deterministically
- maintain internal state (e.g. indicators)
- produce trading signals
- enforce local constraints

---

## Strategy behavior

Strategies:

- consume only canonical market events
- produce raw signals
- must not:
  - access execution
  - access other traders
  - access global state

---

## Risk behavior

Risk module may:

- approve or reject trades
- adjust order size

Risk must not:

- delay trades
- modify market timing decisions

---

## Allocation

- capital is assigned per trader
- no global portfolio optimization in v1

---

## Degraded mode

Trader may enter degraded mode when:

- market data is incomplete
- replay is in progress

In degraded mode:

- no new positions are opened
- existing positions may be managed

---

## Restart behavior

On restart:

1. trader receives replayed events
2. reconstructs internal state
3. resumes live processing

---

## Isolation

- trader must not access other traders
- all state must be local or derived from events
