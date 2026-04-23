# Harness State Machine

## Status

This document is a high-level, human-oriented description of the harness workflow.

It is not normative.

The authoritative behavior is defined in:
- agent/workflow.md
- runbooks/
- scripts/

## State Transtion Table

```
PLANNING
- --[creates selectable implementation task(s)]--> IMPLEMENTATION
- --[only creates/refines planning tasks; no selectable implementation task]--> PLANNING
- --[decides current line is unsound and writes recovery plan]--> RECOVERY
- --[cannot resolve ambiguity safely]--> BLOCKED / ESCALATION

IMPLEMENTATION
  --[task done and more selectable tasks exist]--> IMPLEMENTATION
  --[task done and no selectable implementation task exists]--> PLANNING
  --[blocked by unclear backlog/spec/design]--> PLANNING
  --[detects systemic drift / unsafe direction]--> PLANNING
      note: implementation recommends recovery; planning decides
  --[harness verification/finalization fails]--> BLOCKED / REPAIR

RECOVERY
  --[recovery succeeds and next implementation task is selectable]--> IMPLEMENTATION
  --[recovery succeeds but backlog needs repair/replanning]--> PLANNING
  --[recovery plan invalid or restore fails]--> PLANNING / BLOCKED
```
