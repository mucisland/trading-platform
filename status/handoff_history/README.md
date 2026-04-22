# Session Handoff History

## Purpose

This directory contains archived session handoffs.

Each file represents the outcome of one completed session and serves as the durable history of development progress.

## Structure

- One file per session:

      H-00001.md
      H-00002.md

- IDs are:
  - unique
  - monotonically increasing
  - never reused

## Relationship to current handoff

- `/status/session_handoff.md`
  → current, active session state (hot)

- `/status/handoff_history/`
  → completed session records (cold)

The current handoff must always be overwritten at the end of a session.
It must not be used as a history log.

## Entry format

Each entry is a direct copy of the current handoff artifact at that time, except that an additional section is added at the top, following this format:

    # H-00001

    - archived_from: /status/session_handoff.md
    - timestamp: 2026-04-22T12:34:56Z
