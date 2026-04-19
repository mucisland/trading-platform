# Recovery Runbook

## Purpose

This runbook defines how the workflow restores the repository to a previously trusted state when current progress is judged incorrect, unstable, or misaligned.

It is intended primarily for:
- planning/recovery agents
- the harness
- human maintainers

Implementation agents normally only need to know that recovery mode exists and that they may recommend it.

## Recovery principles

- rollback is a normal workflow control, not an exceptional failure response
- prefer restoring a trusted state over continuing from an untrustworthy one
- choose the smallest rollback that restores confidence
- record recovery decisions explicitly in repository artifacts

## Recovery types

### Tactical recovery
Use when:
- one session or a small recent change set is wrong
- the rest of the line of development is still trustworthy

### Strategic recovery
Use when:
- multiple sessions are based on a bad assumption
- architecture has drifted
- milestone progress has degraded across several commits or merges

## Recovery ownership

### Implementation agent
May:
- detect warning signs
- recommend recovery mode
- record reasons in handoff/backlog

Must not:
- decide rollback scope
- execute rollback

### Planning/recovery agent
Owns:
- deciding whether recovery mode is required
- selecting the rollback target
- deciding whether the recovery is tactical or strategic
- updating planning artifacts after the decision

### Harness
Owns:
- executing rollback or restore actions deterministically
- validating the restored state
- preserving repository consistency

## Recovery inputs

Use:
- `/status/session_handoff.md`
- `/backlog/fix_plan.md`
- `/status/checkpoints.md` if available
- recent validation results
- recent commit history
- milestone status

## Recovery target selection

Prefer a rollback target that is:
- previously validated
- understandable from repository artifacts
- aligned with current milestone goals
- the smallest rollback that restores trust

Prefer explicit checkpoints or milestone-stable states when available.

## Recovery procedure

1. Stop forward implementation work.
2. Record the recovery reason.
3. Determine whether the recovery is tactical or strategic.
4. Select the rollback target.
5. Record the recovery plan in:
   - `/status/session_handoff.md`
   - `/backlog/fix_plan.md`
6. Execute the restore action through the harness.
7. Validate the restored state.
8. Update backlog and handoff with:
   - what was rolled back
   - why it was rolled back
   - validation status after restoration
   - next recommended planning or implementation task

## Documentation requirements

Every recovery must record:
- recovery reason
- rollback target
- affected task(s) or commit range
- validation result after restoration
- next recommended task

## Core principle

Repository history must support safe restoration, not only forward progress.
