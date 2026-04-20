# Recovery History

## Purpose

This directory contains a durable record of all recovery events.

Each recovery represents a decision to restore the repository to a previously trusted state.

Recovery history complements:

- Git history (structural changes)
- session handoffs (local session continuity)

It provides the semantic layer explaining:

- why recovery was needed
- what state was restored
- whether the restored state was validated
- what the next step is

## Structure

Each recovery is stored as a separate file:

    R-00001.md
    R-00002.md
    ...

IDs are:

- unique
- monotonically increasing
- never reused

## When to create a recovery entry

A recovery entry must be created when:

- repository state is rolled back or restored
- recovery mode is executed by the harness

## Relationship to other artifacts

Each recovery must be traceable to:

- a recovery plan artifact
- a session handoff
- a Git commit representing the recovery event

## Core principle

Recovery must be:

- explicit
- reproducible
- auditable
- understandable without relying on chat history
