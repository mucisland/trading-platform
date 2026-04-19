# Agentic Workflow Rationale

## Purpose

This document explains the design principles and reasoning behind the agentic development workflow used in this repository.

It is intended for:
- human maintainers
- future system evolution
- potential planner or meta-agents

It is not required reading for implementation agents during a single development session.

## Core idea

Development is performed as a sequence of independent, bounded sessions.

In each session:
- a single agent works on one scoped task
- context is intentionally limited
- all continuity is carried through repository artifacts

This creates a system where:
- work is restartable
- progress is incremental and controlled
- failure does not corrupt global state

## Why session-based development

### Problem

Large-context, continuous agent execution leads to:
- context drift
- hallucinated assumptions
- loss of grounding in actual code
- accumulation of implicit state

### Solution

Use short, bounded sessions with:
- explicit inputs
- explicit outputs
- no reliance on conversational memory

Each session:
- starts from repository state
- performs one task
- writes back structured artifacts

This aligns with modern harness-based approaches.

## One task per session

### Problem

Agents tend to:
- expand scope
- fix unrelated issues
- perform implicit refactoring
- lose track of original intent

### Solution

Restrict each session to:
- exactly one backlog item
- minimal required changes

Effects:
- clearer reasoning
- easier validation
- predictable progress
- simpler recovery after failure

## Repository as system of record

### Problem

Conversational history is:
- incomplete
- lossy
- not reliably available
- not structured for reasoning

### Solution

All relevant state is stored in the repository:

- backlog → planning state
- handoff → execution continuity
- specs → correctness definitions
- runbooks → procedures
- patterns → learned behavior

Agents must treat:
- repository artifacts as authoritative
- chat history as non-authoritative

## Artifact-driven continuity

### Problem

Without structured handoff:
- each session must rediscover context
- work is duplicated
- progress becomes inconsistent

### Solution

Use explicit artifacts:

- `/status/session_handoff.md` → current execution state
- `/backlog/fix_plan.md` → task selection and planning

Artifacts are:
- structured
- concise
- optimized for fast reconstruction

The current handoff:
- contains only the latest relevant state
- is overwritten each session
- may be archived separately

## Minimal context loading

### Problem

Large context leads to:
- slower reasoning
- higher hallucination risk
- distraction from the task

### Solution

Load only:
- AGENT.md
- one backlog item
- a small number of specs
- one runbook
- relevant source files

Effects:
- faster execution
- better focus
- more deterministic behavior

## Separation of concerns

The system separates rules into distinct layers:

### AGENT.md
- entry point
- instruction hierarchy
- core constraints

### /agent/workflow.md
- general execution behavior
- reusable across projects

### /agent/project_rules.md
- project-specific constraints
- invariants and boundaries

### /agent/patterns.md
- accumulated lessons
- failure patterns and prevention rules

This separation ensures:
- clarity
- reusability
- maintainability

## Restartability as a primary design goal

The system is designed so that:
- any session can fail without corrupting overall progress
- work can resume from artifacts alone
- no hidden in-memory state is required

This applies both to:
- the development workflow
- the trading platform architecture itself

## Validation philosophy

Validation is:
- minimal by default
- escalated when risk increases

Agents:
- must not skip validation
- must not assume correctness
- must treat failed validation as incomplete work

This balances:
- speed
- correctness
- reliability

## Failure handling

Failures are expected.

When a failure occurs:
- do not expand scope
- do not apply large workarounds
- record the failure
- recommend the next smallest task

Failures are converted into:
- backlog items
- patterns (if recurring)

## Continuous improvement

The system improves over time via:

- `/agent/patterns.md`

When:
- a failure repeats
- a better approach is discovered

Then:
- a pattern is recorded
- a rule is derived

This prevents repeated mistakes.

## Why not a single long-running agent

Long-running agents suffer from:
- context accumulation
- implicit state corruption
- non-deterministic behavior
- poor recovery after failure

The session-based model avoids these issues by:
- resetting context regularly
- enforcing explicit state transitions
- keeping reasoning local and verifiable

## Tradeoffs

### Costs
- more explicit artifact management
- additional structure and discipline
- more files and documentation

### Benefits
- high reliability
- strong restartability
- clear progress tracking
- suitability for long-running development

The benefits outweigh the costs for complex systems.

## Summary

This workflow is designed to ensure:

- small, controlled steps
- explicit state transitions
- minimal ambiguity
- strong recovery guarantees

It enables long-running, unattended development without relying on fragile conversational context.

The system is intentionally strict so that:
- agents remain predictable
- progress remains consistent
- failures remain contained

## References

- https://www.anthropic.com/engineering/harness-design-long-running-apps
- https://openai.com/index/harness-engineering
- https://ghuntley.com/ralph
